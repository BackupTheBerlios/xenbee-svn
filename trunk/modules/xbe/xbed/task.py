"""
The XenBEE task module

contains:
    TaskManager:
	used to create new tasks
	manages all currently known tasks
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging, time, threading, os, os.path
log = logging.getLogger(__name__)

try:
    from traceback import format_exc as format_exception
except:
    from traceback import format_exception

from xbe.util import singleton
from xbe.util.exceptions import *
from xbe.util import fsm
from xbe.util.observer import Observable
from xbe import util
from xbe.xbed.task_fsm import TaskFSM
from xbe.xbed.daemon import XBEDaemon
from xbe.xbed.instance import InstanceManager
from xbe.xbed.task_activity_queue import ActivityQueue

from twisted.internet import reactor, defer, threads
from twisted.python import failure

class TaskError(XenBeeException):
    pass

class StopTask(TaskError):
    pass

class Task(TaskFSM):
    def __init__(self, id, mgr):
        """Initialize a new task."""
        TaskFSM.__init__(self)
        self.mtx = self.fsm.getLock()
        self.__timestamps = {}
        self.__timestamps["submit"] = time.time()
        self.__id = id
        self.log = logging.getLogger("task."+self.id())
        self.mgr = mgr

    def id(self):
        return self.__id

    def __repr__(self):
        return "<%(cls)s %(id)s in state %(state)s>" % {
            "cls": self.__class__.__name__,
            "id": self.id(),
            "state": self.state(),
        }

    def signalExecutionEnd(self, exitcode):
        self.mtx.acquire()
        try:
            self.signalExecutionDone(exitcode)
        finally:
            self.mtx.release()

    def signalExecutionFailed(self, reason):
        self.mtx.acquire()
        try:
            self.signalExecutionDone(reason)
        finally:
            self.mtx.release()
        
    def signalExecutionDone(self, result):
        try:
            wait_tuple = self.__executionWaitTuple
        except AttributeError:
            pass
        else:
            wait_tuple[0].acquire()
            try:
                wait_tuple[1] = result
                wait_tuple[0].notify()
            finally:
                wait_tuple[0].release()

    def sendJSDLToInstance(self):
        self.mtx.acquire()
        try:
            self.__inst.protocol.executeTask(self.__jsdl_xml, self)
            self.log.info("task sent to instance")
        finally:
            self.mtx.release()

    def getStatusInfo(self):
        """Return all possible information about this task in a
        dictionary.
        
        The information returned depends on the current state.
        """
        info = {}
        self.mtx.acquire()
        try:
            times = {}
            # timestamp information
            for time, tstamp in self.__timestamps.iteritems():
                times["%s-time" % time] = tstamp
            info["times"] = times
            
            if hasattr(self, 'reason'):
                reason = self.reason
                if isinstance(reason, failure.Failure):
                    msg = reason.getErrorMessage()
                else:
                    msg = str(reason)
                info["reason"] = msg
            if hasattr(self, 'exitcode'):
                info["exitcode"] = self.exitcode

            if self.state() == "Running:Executing":
                # instance is available and has an IP
                info["IP"] = self.__inst.ip
        finally:
            self.mtx.release()
        return info

    #
    # FSM transitions
    # (overrides those defined in TaskFSM)
    #
    def do_confirmed(self, jsdl_xml, jsdl_doc, *args, **kw):
        """The task has been confirmed by the user."""
        self.mtx.acquire()
        try:
            self.__timestamps["confirm"] = time.time()
            self.log.info("confirmed")
            self.__jsdl_xml = jsdl_xml
            self.__jsdl_doc = jsdl_doc
        finally:
            self.mtx.release()

    def do_terminate_pending_reserved(self, reason, *args, **kw):
        """terminate a pending task, that has not been confirmed yet.

        That should not impose much work to do.
        """
        self.mtx.acquire()
        try:
            self.__timestamps["terminate"] = time.time()
            self.reason = reason
            self.log.info("terminating pending reserved: %s" % self.reason_as_str())
        finally:
            self.mtx.release()

    def do_terminate_pending_confirmed(self, reason, *args, **kw):
        """terminate a confirmed task."""
        self.mtx.acquire()
        try:
            self.__timestamps["terminate"] = time.time()
            self.reason = reason
            self.log.info("terminating pending confirmed: %s" % self.reason_as_str())
            del self.__jsdl_xml
            del self.__jsdl_doc
        finally:
            self.mtx.release()

    def do_stage_in(self, *args, **kw):
        """stage in all necessary files and wait for other resources.

        this method must be asynchronous
        addCallback(self.stage_in_completed).addErrback(self.failed)

        pre-cond: task description available and task has been confirmed
        post-cond: state == Running:Stage-In
        """
        self.mtx.acquire()
        try:
            self.__timestamps["stage-in-start"] = time.time()
            rv = self.__prepare()
        finally:
            self.mtx.release()
        return rv

    def do_terminate_stage_in(self, reason, *args, **kw):
        """terminate the stage-in process, must not fail."""
        self.mtx.acquire()
        try:
            self.__timestamps["terminate"] = time.time()
            self.reason = reason
            self.log.info("terminating stage-in: %s" % self.reason_as_str())
            self.__clean_up_spool()
        finally:
            self.mtx.release()

    def do_stage_in_failed(self, reason, *args, **kw):
        """handle the case, that the staging failed"""
        self.mtx.acquire()
        try:
            self.__timestamps["failed"] = time.time()
            self.reason = reason
            self.log.warn("stage-in failed: %s" % self.reason_as_str())
            self.__clean_up_spool()
        finally:
            self.mtx.release()

    def do_start_instance(self, *args, **kw):
        """all files are staged in, so trigger the start of the instance
           addCallback(self.cb_instance_started).addErrback(self.failed)"""
        self.mtx.acquire()
        try:
            self.log.debug("initiating instance startup")
            self.__timestamps["instance-start"] = time.time()
            self.__configureInstance(self.__inst, self.__jsdl_doc)
            self.__start_instance()
        finally:
            self.mtx.release()
        self.log.debug("instance start initiated")

    def do_terminate_instance_starting(self, reason, *args, **kw):
        """terminate the start process of the instance."""
        self.mtx.acquire()
        try:
            self.__timestamps["terminate"] = time.time()
            self.reason = reason
            self.log.info("terminating instance-start: %s" % self.reason_as_str())
            self._cb_release_resources()
            self.__clean_up_spool()
        finally:
            self.mtx.release()

    def do_instance_starting_failed(self, reason, *args, **kw):
        """handle a failed instance start attempt"""
        self.mtx.acquire()
        try:
            self.__timestamps["failed"] = time.time()
            self.reason = reason
            self.log.warn("instance start failed: %s" % self.reason_as_str())
            self._cb_release_resources()
            self.__clean_up_spool()
        finally:
            self.mtx.release()

    def do_execute_task(self, *args, **kw):
        """execute the task
        pre-cond. instance available -> protocol is ready
        post-cond. jsdl sent to instance
        """
        self.mtx.acquire()
        try:
            self.log.info("executing task")
            self.__timestamps["execute"] = time.time()
            self.__execute()
        finally:
            self.mtx.release()

    def do_terminate_execution(self, reason, *args, **kw):
        """terminate the execution within the instance.

        shutdown the instance
        """
        self.mtx.acquire()
        try:
            self.__timestamps["terminate"] = time.time()
            self.reason = reason
            self.log.info("terminating execution: %s" % self.reason_as_str())
            self.__stop_instance()
            self._cb_release_resources()
            self.__clean_up_spool()
        finally:
            self.mtx.release()

    def do_execution_failed(self, reason, *args, **kw):
        """the task execution failed

        that should be something like 'do_stop_instance' with different callbacks
        """
        self.mtx.acquire()
        try:
            self.__timestamps["failed"] = time.time()
            self.reason = reason
            self.log.warn("execution failed: %s" % self.reason_as_str())
            self.__stop_instance()
            self._cb_release_resources()
            self.__clean_up_spool()
        finally:
            self.mtx.release()

    def do_stage_out(self, *args, **kw):
        """task has finished its execution,
           instance has been shut down, stage out the data"""
        self.mtx.acquire()
        try:
            self.log.info("staging out")
            self.__timestamps["stage-out-start"] = time.time()
            rv = self.__unprepare()
        finally:
            self.mtx.release()
        return rv

    def do_stage_out_failed(self, reason, *args, **kw):
        """stage out process failed, so handle that"""
        self.mtx.acquire()
        try:
            self.__timestamps["failed"] = time.time()
            self.reason = reason
            self.log.warn("stage-out failed: %s" % self.reason_as_str())
            self.__clean_up_spool()
        finally:
            self.mtx.release()

    def do_terminate_stage_out(self, reason, *args, **kw):
        """terminate the stage out process"""
        self.mtx.acquire()
        try:
            self.reason = reason
            self.log.info("terminating stage out: %s" % self.reason_as_str())
            self.__timestamps["terminate"] = time.time()
            self.__clean_up_spool()
        finally:
            self.mtx.release()

    def do_task_finished(self, *args, **kw):
        """pre-cond: stage-out is complete"""
        self.mtx.acquire()
        try:
            self.log.info("task finished")
            self.__timestamps["finished"] = time.time()
            self.__clean_up_spool()
        finally:
            self.mtx.release()

    #
    # Helper methods
    #
    # these methods are used internally by the task
    #

    def reason_as_str(self):
        if isinstance(self.reason, failure.Failure):
            msg = self.reason.getErrorMessage()
        else:
            msg = str(self.reason)
        return msg
    
    def __createSpool(self):
        """Creates the spool-directory for this task.

        The spool looks something like that: <spool>/UUID(task)/

        The spool directory is used to store all necessary information
        about this task:
	    * kernel, root, swap, image
	    * persistent configuration
	    * access and security stuff
            * anything other that makes sense

        raises OSError, if the spool could not be created.
        returns the complete path
        """
        import os, os.path
        
        path = os.path.normpath(os.path.join(self.mgr.spool, self.id()))
        # create the directory structure
        os.makedirs(path)
        return path

    def __clean_up_spool(self, *a, **kw):
        """cleans up the task, i.e. removes the task's spool directory"""
        self.log.info("removing spool directory")
        from xbe.util import removeDirCompletely
        removeDirCompletely(self.__spool)

    def _cb_assign_mac_ip_to_inst(self, mac_ip):
        inst = self.__inst
        self.log.debug(
            "assigning mac '%s' with IP '%s' to instance: %s" % (mac_ip[0], mac_ip[1], inst.id()))
        inst.config().setMac(mac_ip[0])
        inst.ip = mac_ip[1]

    def _cb_assign_files_to_inst(self):
        inst = self.__inst
        spool = os.path.join(self.__spool, "jail", "var", "xbe-spool")

        # images, kernel and probably initrd
        images = []
        images.append(os.path.join(spool, "image"))
        images.append(os.path.join(spool, "swap"))
        for dir_entry in os.listdir(spool):
            path = os.path.join(spool, dir_entry)
            if os.path.isfile(path) and \
               path.endswith(".img"):
                images.append(path)

        for ctr in xrange(len(images)):
            inst.config().addDisk(images[ctr], "sda%d" % (ctr+1,))
        
        path = os.path.join(spool, "kernel")
        inst.config().setKernel(path)

        path = os.path.join(spool, "initrd")
        if os.path.exists(path):
            inst.config().setInitrd(path)

    def _cb_store_exitcode(self, exitcode):
        self.exitcode = exitcode

    def __configureInstance(self, inst, jsdl):
        # set the uri through which i am reachable
        inst.config().addToKernelCommandLine(XBE_SERVER="%s" % (
            XBEDaemon.getInstance().opts.uri
        ))
        inst.config().addToKernelCommandLine(XBE_UUID="%s" % (
            inst.id()
        ))
        try:
            ncpus = int(jsdl.lookup_path("JobDefinition/JobDescription/Resources/"+
                                         "TotalCPUCount").get_value())
        except Exception, e:
            self.log.debug("using default number of cpus: 1", e)
            ncpus = 1
        inst.config().setNumCpus(ncpus)

        try:
            pmem = int(jsdl.lookup_path("JobDefinition/JobDescription/Resources/"+
                                        "TotalPhysicalMemory").get_value())
        except Exception, e:
            self.log.debug("using default memory: 134217728", e)
            pmem = 134217728
        inst.config().setMemory(pmem)
        return inst

    def _cb_release_resources(self):
        self.log.info("releasing acquired resources")
        mac_ip = (self.__inst.config().getMac(), self.__inst.ip)
        XBEDaemon.getInstance().macAddresses.release(mac_ip)
        self.__delete_instance()
        log.info("resources released")

    def __delete_instance(self, *a, **kw):
        InstanceManager.getInstance().removeInstance(self.__inst)
        del self.__inst.task
        del self.__inst

    def __prepare(self):
        self.log.debug("initiating preparation")

        # create the spool directory
        self.__spool = self.__createSpool()

        # create the instance
        self.__inst = InstanceManager.getInstance().newInstance(self.__spool)
        self.__inst.task = self

        from xbe.xbed.task_activities import SetUpActivity, AcquireResourceActivity
        from xbe.util.activity import ComplexActivity, ThreadedActivity

        mac_pool = XBEDaemon.getInstance().macAddresses
        jail_package = XBEDaemon.getInstance().opts.jail_package
        mac_acquirer = ThreadedActivity(
            AcquireResourceActivity(mac_pool))
        setup_activity = ThreadedActivity(
            SetUpActivity(self.__spool, jail_package), (self.__jsdl_doc,))

        complex_activity = ComplexActivity([setup_activity, mac_acquirer])
        self.mgr.registerActivity(self, complex_activity,
                                  on_finish=self._cb_stage_in_succeed,
                                  on_fail=self._eb_stage_in_failed,
                                  on_abort=None)

    def _cb_stage_in_succeed(self, results, *a, **kw):
        try:
            self.mtx.acquire()
            mac_ip = results[1]
            self._cb_assign_mac_ip_to_inst(mac_ip)
            self._cb_assign_files_to_inst()
        finally:
            self.mtx.release()
        self.log.debug("stage in completed")
        self.cb_stage_in_completed()

    def _eb_stage_in_failed(self, results, *a, **kw):
        try:
            self.mtx.acquire()
            self.failed(results[0])
        finally:
            self.mtx.release()
        
    def __unprepare(self):
        self.log.debug("starting un-preparation")
        from xbe.xbed.task_activities import TearDownActivity
        from xbe.util.activity import ComplexActivity, ThreadedActivity

        teardown_activity = ThreadedActivity(
            TearDownActivity(self.__spool), (self.__jsdl_doc,))

        complex_activity = ComplexActivity([teardown_activity])
        self.mgr.registerActivity(self, complex_activity,
                                  on_finish=self._cb_stage_out_succeed,
                                  on_fail=self._eb_stage_out_failed,
                                  on_abort=None)

    def _cb_stage_out_succeed(self, results, *a, **kw):
        try:
            self.mtx.acquire()
        finally:
            self.mtx.release()
        self.log.debug("stage out completed")
        self.cb_stage_out_completed()

    def _eb_stage_out_failed(self, results, *a, **kw):
        try:
            self.mtx.acquire()
        finally:
            self.mtx.release()
        self.failed(results[0])

    def __start_instance(self):
        from xbe.xbed.task_activities import StartInstanceActivity
        from xbe.util.activity import ComplexActivity, ThreadedActivity
 
        # start the instance with a 3 minute timeout
        instance_starter = ThreadedActivity(
            StartInstanceActivity(self.__inst), (3*60,))

        complex_activity = ComplexActivity([instance_starter])
        self.mgr.registerActivity(self, complex_activity,
                                  on_finish=self._cb_instance_start_succeed,
                                  on_fail=self._eb_instance_start_failed,
                                  on_abort=None)

    def _cb_instance_start_succeed(self, result, *a, **kw):
        try:
            self.mtx.acquire()
        finally:
            self.mtx.release()
        self.log.debug("instance successfully started")
        self.cb_instance_started()

    def _eb_instance_start_failed(self, results, *a, **kw):
        try:
            self.mtx.acquire()
        finally:
            self.mtx.release()
        self.failed(results[0])

    def __stop_instance(self):
        # this is un-interruptable
        if not self.__inst.is_stopped():
            try:
                self.__inst.stop()
            except Exception, e:
                assert(False, "instance::stop() is not supposed to raise any exception")
        
    def _cb_execution_finished(self, result):
        try:
            self.mtx.acquire()
            self.__stop_instance()
            self._cb_release_resources()
            self.cb_execution_finished()
        finally:
            self.mtx.release()

    def __execute(self):
        try:
            from xbe.xbed.task_activities import ExecutionActivity
            from xbe.util.activity import ComplexActivity, ThreadedActivity

            self.__executionWaitTuple = [threading.Condition(), None]
            execution_waiter = ThreadedActivity(
                ExecutionActivity(self, self.__executionWaitTuple))
            complex_activity = ComplexActivity([execution_waiter])
            self.mgr.registerActivity(self, complex_activity,
                                      on_finish=self.cb_execution_finished,
                                      on_fail=self.failed,
                                      on_abort=None)
        except Exception, e:
            log.debug("execution failed: %s" % e)
        
class TaskManager(singleton.Singleton, Observable):
    """The task-manager.

    Through this class every known task can be controlled:
	- create new tasks

    """
    def __init__(self, daemon, spool):
        """Initialize the TaskManager."""
        singleton.Singleton.__init__(self)
        Observable.__init__(self)
        self.spool = spool
        self.tasks = {}
        self.mtx = threading.RLock()
        self.daemon = daemon
        self.activityQueue = ActivityQueue()

    def new(self):
        """Returns a new task."""
        from xbe.util.uuid import uuid
        self.mtx.acquire()

        task = Task(uuid(), self)

        self.tasks[task.id()] = task
        self.mtx.release()

        self.notify( (task, "newTask") )
        return task

    def removeTask(self, task):
        """Remove the 'task' from the manager."""
        try:
            self.mtx.acquire()
            self.tasks.pop(task.id())
            del task.mgr
            self.notify( (task, "removeTask") )
        finally:
            self.mtx.release()

    def registerActivity(self, task, activity, on_finish, on_fail, on_abort):
        log.debug("registering new activity %s for task %s" % (repr(activity), task.id()))
        self.activityQueue.registerActivity(task, activity,
                                            on_finish, on_fail, on_abort)

    def abortActivities(self, task):
        self.activityQueue.abortActivities(task)

    def lookupByID(self, id):
        """Return the task for the given ID.

        returns the task object or None

        """
        return self.tasks.get(id)

    def terminateTask(self, task, reason):
        self.abortActivities(task)
        task.terminate(reason)

    def taskFailed(self, task):
        """Called when a task has failed somehow."""
        self.notify( (task, "taskFailed") )

    def taskReady(self, task):
        """Called when a task says, that it's ready."""
        self.notify( (task, "taskReady") )

    def taskFinished(self, task):
        """Called when a task finished."""
        self.notify( (task, "taskFinished") )

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
from xbe import util
from xbe.util import fsm
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
        self.mtx = threading.RLock()
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

    def getStatusInfo(self):
        """Return all possible information about this task in a
        dictionary.
        
        The information returned depends on the current state.
        """
        info = {}
        # timestamp information
        for time, tstamp in self.__timestamps.iteritems():
            info["%s-time" % time] = tstamp

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
            if isinstance(reason, failure.Failure):
                msg = reason.getErrorMessage()
            else:
                msg = str(reason)
            self.log.info("terminating pending reserved: %s" % msg)
        finally:
            self.mtx.release()

    def do_terminate_pending_confirmed(self, reason, *args, **kw):
        """terminate a confirmed task."""
        self.mtx.acquire()
        try:
            self.__timestamps["terminate"] = time.time()
            self.reason = reason
            if isinstance(reason, failure.Failure):
                msg = reason.getErrorMessage()
            else:
                msg = str(reason)
            self.log.info("terminating pending confirmed: %s" % msg)
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
            if isinstance(reason, failure.Failure):
                msg = reason.getErrorMessage()
            else:
                msg = str(reason)
            self.log.info("terminating stage-in: %s" % msg)
            self.mgr.abortActivities(self)
            self.__clean_up_spool()
        finally:
            self.mtx.release()

    def do_stage_in_failed(self, reason, *args, **kw):
        """handle the case, that the staging failed"""
        self.mtx.acquire()
        try:
            self.__timestamps["failed"] = time.time()
            self.reason = reason
            if isinstance(reason, failure.Failure):
                msg = reason.getErrorMessage()
            else:
                msg = str(reason)
            self.log.warn("stage-in failed: %s" % msg)
            self.__clean_up_spool()
        finally:
            self.mtx.release()

    def do_start_instance(self, *args, **kw):
        """all files are staged in, so trigger the start of the instance
           addCallback(self.cb_instance_started).addErrback(self.failed)"""
        self.mtx.acquire()
        try:
            self.__timestamps["instance-start"] = time.time()
            self.__configureInstance(self.__inst, self.__jsdl_doc)
            self.__inst.start().addCallback(self.cb_instance_started).\
                                addErrback(self.failed)
        finally:
            self.mtx.release()

    def do_terminate_instance_starting(self, reason, *args, **kw):
        """terminate the start process of the instance."""
        self.mtx.acquire()
        try:
            self.__timestamps["terminate"] = time.time()
            self.reason = reason
            if isinstance(reason, failure.Failure):
                msg = reason.getErrorMessage()
            else:
                msg = str(reason)
            self.log.info("terminating instance-start: %s" % msg)
        finally:
            self.mtx.release()

    def do_instance_starting_failed(self, reason, *args, **kw):
        """handle a failed instance start attempt"""
        self.mtx.acquire()
        try:
            self.__timestamps["failed"] = time.time()
            self.reason = reason
            if isinstance(reason, failure.Failure):
                msg = reason.getErrorMessage()
            else:
                msg = str(reason)
            self.log.warn("instance start failed: %s" % msg)
            self.__stop_instance(self.__inst)
        finally:
            self.mtx.release()

    def do_execute_task(self, *args, **kw):
        """execute the task
        pre-cond. instance available -> protocol is ready
        post-cond. jsdl sent to instance
        """
        self.mtx.acquire()
        try:
            self.__timestamps["execute"] = time.time()
            log.info("executing task")
            self.__inst.protocol.executeTask(
                self.__jsdl_xml, self).\
                addCallback(self._cb_store_exitcode).\
                addCallback(self.cb_execution_finished).\
                addErrback(self.failed)
        finally:
            self.mtx.release()

    def do_terminate_execution(self, reason, *args, **kw):
        """terminate the execution within the instance.

        1. terminate the task within the instance
        2. shutdown the instance
        """
        self.mtx.acquire()
        try:
            self.__timestamps["terminate"] = time.time()
            self.reason = reason
            if isinstance(reason, failure.Failure):
                msg = reason.getErrorMessage()
            else:
                msg = str(reason)
            self.log.info("terminating execution: %s" % msg)
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
            if isinstance(reason, failure.Failure):
                msg = reason.getErrorMessage()
            else:
                msg = str(reason)
            self.log.warn("execution failed: %s" % msg)
            self.__stop_instance(self.__inst)
        finally:
            self.mtx.release()

    def do_stop_instance(self, *args, **kw):
        """the task has finished its execution stop the instance"""
        self.mtx.acquire()
        try:
            self.log.info("stopping instance")
            self.__timestamps["instance-stop"] = time.time()
            self.__stop_instance(self.__inst).addCallback(self.cb_instance_stopped)
        finally:
            self.mtx.release()

    def do_terminate_instance_stopping(self, reason, *args, **kw):
        """terminate the shutdown-process
        I think that has to be a 'noop', but the 'instance-stopped' callback
        must not do any harm!"""
        self.mtx.acquire()
        try:
            self.__timestamps["terminate"] = time.time()
            self.reason = reason
            if isinstance(reason, failure.Failure):
                msg = reason.getErrorMessage()
            else:
                msg = str(reason)
            self.log.info("terminate instance-stop: %s" % msg)
        finally:
            self.mtx.release()

    def do_instance_stopping_failed(self, reason, *args, **kw):
        """i really do not know, what to do about that, maybe force the destroying"""
        self.mtx.acquire()
        try:
            self.__timestamps["failed"] = time.time()
            self.reason = reason
            if isinstance(reason, failure.Failure):
                msg = reason.getErrorMessage()
            else:
                msg = str(reason)
            self.log.warn("instance-stop failed: %s" % msg)
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
            self.reason = reason
            self.__timestamps["failed"] = time.time()
            if isinstance(reason, failure.Failure):
                msg = reason.getErrorMessage()
            else:
                msg = str(reason)
            self.log.warn("stage-out failed: %s" % msg)
            self.__clean_up_spool()
        finally:
            self.mtx.release()

    def do_terminate_stage_out(self, reason, *args, **kw):
        """terminate the stage out process"""
        self.mtx.acquire()
        try:
            self.__timestamps["terminate"] = time.time()
            self.reason = reason
            if isinstance(reason, failure.Failure):
                msg = reason.getErrorMessage()
            else:
                msg = str(reason)
            self.log.info("terminating stage out: %s" % msg)
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
        spool = self.__spool

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

    def __stop_instance(self, inst):
        """returns a deferred"""
        return inst.stop().addErrback(
            self.__inst.destroy).addCallback(self._cb_release_resources)

    def _cb_release_resources(self, arg):
        self.log.info("releasing acquired resources")
        mac_ip = (self.__inst.config().getMac(), self.__inst.ip)
        XBEDaemon.getInstance().macAddresses.release(mac_ip)
        self.__delete_instance()
        log.info("resources released")
        return arg

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
        from xbe.util.activity import ComplexActivity, ThreadedActivity, HOOK_SUCCESS

        mac_pool = XBEDaemon.getInstance().macAddresses
        mac_acquirer = ThreadedActivity(
            AcquireResourceActivity(mac_pool))
        setup_activity = ThreadedActivity(
            SetUpActivity(self.__spool), (self.__jsdl_doc,))

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
            self.log.warn(results)
        finally:
            self.mtx.release()
        self.failed()
        
    def __unprepare(self):
        self.log.debug("starting un-preparation")

        # unprepare the task (i.e. stage-out)
        from xbe.xbed import task_unpreparer
        unpreparer = task_unpreparer.UnPreparer()

        d = threads.deferToThread(unpreparer.unprepare,
                                  self.__spool, self.__jsdl_doc)
        d.addCallback(self.cb_stage_out_completed)
        d.addErrback(self.failed)

    def _cb_check_deferred_list(self, results):
        for code, result in results:
            if code == defer.FAILURE:
                return result

class TaskManager(singleton.Singleton):
    """The task-manager.

    Through this class every known task can be controlled:
	- create new tasks

    """
    def __init__(self, daemon, spool):
        """Initialize the TaskManager."""
        singleton.Singleton.__init__(self)
        self.spool = spool
        self.tasks = {}
        self.mtx = threading.RLock()
        self.daemon = daemon
        self.observers = [] # they are called when a new task has been created
        self.activityQueue = ActivityQueue()

    def notify(self, task, event):
        for observer, args, kw in self.observers:
            reactor.callLater(0.5, observer, task, event, *args, **kw)

    def addObserver(self, observer, *args, **kw):
        self.observers.append( (observer, args, kw) )

    def new(self):
        """Returns a new task."""
        from xbe.util.uuid import uuid
        self.mtx.acquire()

        task = Task(uuid(), self)

        self.tasks[task.id()] = task
        self.mtx.release()

        self.notify(task, "newTask")
        return task

    def removeTask(self, task):
        """Remove the 'task' from the manager."""
        try:
            self.mtx.acquire()
            self.tasks.pop(task.id())
            del task.mgr
            self.notify(task, "removeTask")
        finally:
            self.mtx.release()

    def registerActivity(self, task, activity, on_finish, on_fail, on_abort):
        self.activityQueue.registerActivity(task, activity,
                                            on_finish, on_fail, on_abort)

    def abortActivities(self, task):
        self.activityQueue.abortActivities(task)

    def lookupByID(self, id):
        """Return the task for the given ID.

        returns the task object or None

        """
        return self.tasks.get(id)

    def taskFailed(self, task):
        """Called when a task has failed somehow."""
        self.notify(task, "taskFailed")

    def taskReady(self, task):
        """Called when a task says, that it's ready."""
        self.notify(task, "taskReady")

    def taskFinished(self, task):
        """Called when a task finished."""
        self.notify(task, "taskFinished")


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
        self.__tstamp = time.time()
        self.__id = id
        self.log = logging.getLogger("task."+self.id())
        self.mgr = mgr

    def id(self):
        return self.__id

    def submitTime(self):
        return self.__tstamp

    def __repr__(self):
        return "<%(cls)s %(id)s in state %(state)s>" % {
            "cls": self.__class__.__name__,
            "id": self.id(),
            "state": self.state(),
        }

    #
    # FSM transitions
    # (overrides those defined in TaskFSM)
    #
    def do_confirmed(self, jsdl_xml, jsdl_doc, *args, **kw):
        """The task has been confirmed by the user."""
        self.mtx.acquire()
        self.__jsdl_xml = jsdl_xml
        self.__jsdl_doc = jsdl_doc
        self.mtx.release()

    def do_terminate_pending_reserved(self, reason, *args, **kw):
        """terminate a pending task, that has not been confirmed yet.

        That should not impose much work to do.
        """
        self.mtx.acquire()
        self.mtx.release()

    def do_terminate_pending_confirmed(self, reason, *args, **kw):
        """terminate a confirmed task."""
        self.mtx.acquire()
        self.mtx.release()

    def do_stage_in(self, *args, **kw):
        """stage in all necessary files and wait for other resources.

        this method must be asynchronous
        addCallback(self.stage_in_completed).addErrback(self.failed)

        pre-cond: task description available and task has been confirmed
        post-cond: state == Running:Stage-In
        """
        self.mtx.acquire()
        rv = self.__prepare()
        self.mtx.release()
        return rv

    def do_terminate_stage_in(self, reason, *args, **kw):
        """terminate the stage-in process, must not fail."""
        self.mtx.acquire()
        self.mtx.release()

    def do_stage_in_failed(self, reason, *args, **kw):
        """handle the case, that the staging failed"""
        self.mtx.acquire()
        try:
            self.log.warn("stage in failed")
            self.__clean_up()
        finally:
            self.mtx.release()

    def do_start_instance(self, *args, **kw):
        """all files are staged in, so trigger the start of the instance
           addCallback(self.cb_instance_started).addErrback(self.failed)"""
        self.__inst.start().addCallback(self.cb_instance_started).\
                            addErrback(self.failed)

    def do_terminate_instance_starting(self, reason, *args, **kw):
        """terminate the start process of the instance."""
        self.mtx.acquire()
        self.mtx.release()

    def do_instance_starting_failed(self, reason, *args, **kw):
        """handle a failed instance start attempt"""
        self.mtx.acquire()
        try:
            self.log.warn("starting of my instance failed: %s" % reason.getErrorMessage())
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
            self.__inst.protocol.executeTask(self.__jsdl_xml, self)
        finally:
            self.mtx.release()

    def do_terminate_execution(self, reason, *args, **kw):
        """terminate the execution within the instance.

        1. terminate the task within the instance
        2. shutdown the instance
        """
        self.mtx.acquire()
        self.mtx.release()

    def do_execution_failed(self, reason, *args, **kw):
        """the task execution failed

        that should be something like 'do_stop_instance' with different callbacks
        """
        self.mtx.acquire()
        self.mtx.release()

    def do_stop_instance(self, *args, **kw):
        """the task has finished its execution stop the instance"""
        self.mtx.acquire()
        try:
            self.__stop_instance(self.__inst).addCallback(self.cb_instance_stopped)
        finally:
            self.mtx.release()

    def do_terminate_instance_stopping(self, reason, *args, **kw):
        """terminate the shutdown-process
        I think that has to be a 'noop', but the 'instance-stopped' callback
        must not do any harm!"""
        self.mtx.acquire()
        self.mtx.release()

    def do_instance_stopping_failed(self, reason, *args, **kw):
        """i really do not know, what to do about that, maybe force the destroying"""
        self.mtx.acquire()
        self.mtx.release()

    def do_stage_out(self, *args, **kw):
        """task has finished its execution,
           instance has been shut down, stage out the data"""
        self.mtx.acquire()
        self.mtx.release()

    def do_stage_out_failed(self, reason, *args, **kw):
        """stage out process failed, so handle that"""
        self.mtx.acquire()
        self.mtx.release()

    def do_terminate_stage_out(self, *args, **kw):
        """terminate the stage out process"""
        self.mtx.acquire()
        self.mtx.release()

    def do_task_finished(self):
        """pre-cond: stage-out is complete"""
        self.mtx.acquire()
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
	    * kernel, root, swap, additional images
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

    def _cb_assign_mac_to_inst(self, mac, inst):
        inst.config().setMac(mac)

    def _cb_assign_files_to_inst(self, prepare_result, inst, spool):
        # image, kernel and probably initrd
        path = os.path.join(spool, "image")
        inst.config().addDisk(path, "sda1")

        path = os.path.join(spool, "swap")
        if os.path.exists(path):
            inst.config().addDisk(path, "sda2")
        
        path = os.path.join(spool, "kernel")
        inst.config().setKernel(path)

        path = os.path.join(spool, "initrd")
        if os.path.exists(path):
            inst.config().setInitrd(path)

    def __configureInstance(self, inst, jsdl):
        # set the uri through which i am reachable
        inst.config().addToKernelCommandLine(XBE_SERVER="%s" % (
            XBEDaemon.getInstance().opts.uri
        ))
        inst.config().addToKernelCommandLine(XBE_UUID="%s" % (
            inst.id()
        ))
        try:
            ncpus = jsdl.lookup_path("JobDefinition/JobDescription/Resources/"+
                                     "TotalCPUCount").get_value()
        except Exception, e:
            self.log.debug("using default number of cpus: 1", e)
            ncpus = 1
        inst.config().setNumCpus(ncpus)
        return inst

    def __stop_instance(self, inst):
        """returns a deferred"""
        return inst.stop().addErrback(
            self.__inst.destroy).addCallback(self.__release_resources)

    def __release_resources(self, arg):
        self.log.info("releasing acquired resources")
        d = defer.maybeDeferred(XBEDaemon.getInstance().macAddresses.release, self.__inst.config().getMac())
        d.addCallback(self.__delete_instance)
        d.addCallback(self.__clean_up)
        d.addCallback(lambda x: log.info("resources released"))
        return arg

    def __delete_instance(self, *a, **kw):
        InstanceManager.getInstance().removeInstance(self.__inst)
        del self.__inst.task
        del self.__inst

    def __clean_up(self, *a, **kw):
        """cleans up the task, i.e. removes the task's spool directory"""
        from xbe.util import removeDirCompletely
        removeDirCompletely(self.__spool)

    def __prepare(self):
        self.log.debug("starting preparation of task %s" % (self.id(),))

        # create the spool directory
        self.__spool = self.__createSpool()

        # create the instance
        self.__inst = InstanceManager.getInstance().newInstance(self.__spool)
        self.__inst.task = self

        # prepare the task (i.e. stage-in)
        from xbe.xbed import task_preparer
        preparer = task_preparer.Preparer()

        # replace cache uri's with their real ones
        

        d1 = threads.deferToThread(preparer.prepare,
                                  self.__spool, self.__jsdl_doc)
        d1.addCallback(self._cb_assign_files_to_inst, self.__inst, self.__spool)

        # assign a mac address
        d2 = defer.maybeDeferred(XBEDaemon.getInstance().macAddresses.acquire)
        d2.addCallback(self._cb_assign_mac_to_inst, self.__inst)

        d3 = defer.maybeDeferred(self.__configureInstance, self.__inst, self.__jsdl_doc)

        dlist = defer.DeferredList([d1, d2, d3])
        dlist.addCallback(self._cb_check_deferred_list)
        dlist.addCallback(self.cb_stage_in_completed)
        dlist.addErrback(self.failed)

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


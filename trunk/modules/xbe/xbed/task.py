"""
The XenBEE task module

contains:
    TaskManager:
	used to create new tasks
	manages all currently known tasks
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging, time, threading
log = logging.getLogger(__name__)

try:
    from traceback import format_exc as format_exception
except:
    from traceback import format_exception

from xbe.util.exceptions import *
from xbe import util
from xbe.util import fsm
from xbe.xbed.task_fsm import TaskFSM

from twisted.internet import reactor, defer
from twisted.python import failure

class TaskError(XenBeeException):
    pass

class StopTask(TaskError):
    pass

class Task(TaskFSM):
    def __init__(self, id, mgr):
        """Initialize a new task."""
        TaskFSM.__init__(self)
        self.tstamp = time.time()
        self.__id = id
        self.mgr = mgr

    def ID(self):
        """Return the ID for this task."""
        return self.__id

    #
    # FSM transitions
    # (overrides those defined in TaskFSM)
    #
    def do_confirmed(self, *args, **kw):
        """The task has been confirmed by the user."""
        pass

    def do_terminate_pending_reserved(self, reason, *args, **kw):
        """terminate a pending task, that has not been confirmed yet.

        That should not impose much work to do.
        """
        pass

    def do_terminate_pending_confirmed(self, reason, *args, **kw):
        """terminate a confirmed task."""
        pass

    def do_stage_in(self, *args, **kw):
        """stage in all necessary files and wait for other resources.

        this method must be asynchronous
        addCallback(self.stage_in_completed).addErrback(self.failed)

        pre-cond: task description available and task has been confirmed
        post-cond: state == Running:Stage-In
        """
        pass

    def do_terminate_stage_in(self, reason, *args, **kw):
        """terminate the stage-in process, must not fail."""
        pass

    def do_stage_in_failed(self, reason, *args, **kw):
        """handle the case, that the staging failed"""
        pass

    def do_start_instance(self, *args, **kw):
        """all files are staged in, so trigger the start of the instance
           addCallback(self.cb_instance_started).addErrback(self.failed)"""
        pass

    def do_terminate_instance_starting(self, reason, *args, **kw):
        """terminate the start process of the instance."""
        pass

    def do_instance_starting_failed(self, reason, *args, **kw):
        """handle a failed instance start attempt"""
        pass

    def do_execute_task(self, *args, **kw):
        """execute the task
        pre-cond. instance available -> protocol is ready
        post-cond. jsdl sent to instance
        """
        pass

    def do_terminate_execution(self, reason, *args, **kw):
        """terminate the execution within the instance.

        1. terminate the task within the instance
        2. shutdown the instance
        """
        pass

    def do_execution_failed(self, reason, *args, **kw):
        """the task execution failed

        that should be something like 'do_stop_instance' with different callbacks
        """
        pass

    def do_stop_instance(self, *args, **kw):
        """the task has finished its execution stop the instance"""
        pass

    def do_terminate_instance_stopping(self, reason, *args, **kw):
        """terminate the shutdown-process
        I think that has to be a 'noop', but the 'instance-stopped' callback
        must not do any harm!"""
        pass

    def do_instance_stopping_failed(self, reason, *args, **kw):
        """i really do not know, what to do about that, maybe force the destroying"""
        pass

    def do_stage_out(self, *args, **kw):
        """task has finished its execution,
           instance has been shut down, stage out the data"""
        pass

    def do_stage_out_failed(self, reason, *args, **kw):
        """stage out process failed, so handle that"""
        pass

    def do_terminate_stage_out(self, *args, **kw):
        """terminate the stage out process"""
        pass

    def do_task_finished(self):
        """pre-cond: stage-out is complete"""
        pass

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
        
        path = os.path.normpath(os.path.join(self.mgr.spool, self.ID()))
        # create the directory structure
        os.makedirs(path)
        return path

    def __prepare(self):
        log.debug("starting preparation of task %s" % (self.ID(),))

        from xbe.xml import xsdl

        inst_desc = self.document.find("./"+xsdl.XSDL("InstanceDefinition"))

        # create spool for task and instance and prepare it
        task.spool = self.createSpool(task.ID())
        inst = self.instanceManager.newInstance(inst_desc, task.spool)

        task.inst, inst.task = inst, task
        d = inst.prepare()
        
        def _s(arg):
            task.filesRetrieved()
            return task
        def _f(err):
            log.info("file retrieval failed")
            return err
        d.addCallback(_s).addErrback(_f)
        return d


#    # FSM callbacks
#    def do_failed(self, reason):
#        self.endTime = time.time()
#        self.failReason = reason
#        
#        def instStopped(result):
#            if isinstance(result, failure.Failure):
#                log.fatal("stopping backend instance failed: %s" % result)
#            else:
#                log.info("backend stopped.")
#            return self
#        if self.inst.keep_running:
#            log.debug("keeping the instance alive")
#            return defer.succeed(self).addBoth(instStopped)
#        else:
#            return self.inst.stop().addBoth(instStopped)
#
#    def do_prepare(self):
#        return self.mgr.prepareTask(self)
#
#    def do_pending(self):
#        log.info("files for task have been retrieved")
#
#    def do_startInstance(self):
#        d = self.inst.start()
#        def _s(arg):
#            self.instanceAvailable()
#            return self
#        def _f(err):
#            log.error("starting of my instance failed %s" % (err))
#            return err
#        d.addCallback(_s).addErrback(_f)
#        return d
#
#    def do_instanceAvailable(self):
#        log.debug("my instance has been started")
#        self.mgr.taskReady(self)
#
#    def do_execute(self):
#        self.startTime = time.time()
#        log.info("executing task %s" % (self.ID()))
#        self.inst.protocol.executeTask(task=self)
#
#    def do_finished(self, exitcode):
#        self.endTime = time.time()
#        self.exitCode = exitcode
#        def _s(result):
#            self.mgr.taskFinished(self)
#            return self
#        if self.inst.keep_running:
#            log.debug("keeping the instance alive")
#            return defer.succeed(self).addBoth(_s)
#        else:
#            return self.inst.stop().addBoth(_s)
        
class TaskManager:
    """The task-manager.

    Through this class every known task can be controlled:
	- create new tasks

    """
    def __init__(self, daemon, spool):
        """Initialize the TaskManager."""
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

    def newTask(self):
        """Returns a new task."""
        from xbe.util.uuid import uuid
        self.mtx.acquire()

        task = Task(uuid(), self)

        self.tasks[task.ID()] = task
        self.mtx.release()

        self.notify(task, "newTask")
        return task

    def removeTask(self, task):
        """Remove the 'task' from the manager."""
        try:
            self.mtx.acquire()
            self.tasks.pop(task.ID())
            task.mgr = None
            self.notify(task, "removeTask")
        finally:
            self.mtx.release()

    def lookupByID(self, ID):
        """Return the task for the given ID.

        returns the task object or None

        """
        return self.tasks.get(ID)

    def taskFailed(self, task):
        """Called when a task has failed somehow."""
        self.notify(task, "taskFailed")

    def taskReady(self, task):
        """Called when a task says, that it's ready."""
        self.notify(task, "taskReady")

    def taskFinished(self, task):
        """Called when a task finished."""
        self.notify(task, "taskFinished")


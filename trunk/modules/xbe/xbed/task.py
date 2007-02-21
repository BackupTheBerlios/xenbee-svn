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

from twisted.internet import reactor, defer
from twisted.python import failure

class TaskError(XenBeeException):
    pass

class StopTask(TaskError):
    pass

class Task(object):
    def __init__(self, ID, mgr, doc):
        """Initialize a new task."""
        self._id = ID
        self.tstamp = time.time()
        self.mgr = mgr
        self.document = doc
        self.inst = None
        self.instanceWaiter = None # defer activated, when the backend instance is available

        # build FSM
        m = fsm.FSM()
        m.newState("Failed")                      # the task failed
        m.newState("Terminated")                  # the task has been terminated by the user
        m.newState("Pending:Reserved")            # initial state
        m.newState("Pending:Confirmed")           # the task has been confirmed by the user
        m.newState("Running:Stage-In")            # the task is 'running' and stages its files
        m.newState("Running:Executing")           # the task is really executing
        m.newState("Running:Instance-Starting")   # staging complete, instance is starting up
        m.newState("Running:Stage-Out")           # task has ended and files are beeing staged out
        m.newState("Finished")                    # the task is completely finished

        #
        #
        #
        # *----------* confirm  +-----------+
        # | Pending  |--------->| Pending   |----->...
        # | Reserved |          | Confirmed |
        # *----------*          +-----------+
        #       \                 /
        #        \               /
        #         +-------------+
        #         | Terminated  |
        #         +-------------+
        m.setStartState("Pending:Reserved")
        m.addTransition("Pending:Reserved",    # src
                        "Pending:Confirmed",   # dst
                        "confirm_token", self.do_confirmed) # trigger
        m.addTransition("Pending:Reserved",
                        "Terminated",
                        "terminate_token", self.do_terminate_pending_reserved)
        m.addTransition("Pending:Confirmed",
                        "Terminated",
                        "terminate_token", self.do_terminate_pending_confirmed)
        m.addTransition("Pending:Confirmed",
                        "Running:Stage-In",
                        "start_token", self.do_stage_in)
#
#
#
#                                 +----------+
#                +--------------->|  Failed  |<--------------+------------------+----------+
#                |                +----------+               |                  |          |
#                |stage in            ^ inst                 | exec             |          |stage out
#                | failed             |failed                |failed            |          | failed
#                |                    |                      |                  |          |
#  start  +------+---+ stagein +------+-------+ instance +---+-----+ exec    +-------+ +---+-----+
# ------->|  Running |-------->|   Running    |--------->| Running |-------->|Running|-|Running  |--->..
#         | Stage-In |completed|inst starting | started  |Executing|finished |  stop | |Stage-Out|
#         +------+---+         +------+-------+          +----+----+         |  inst | +----+----+
#                |                    |                       |              +-------+      |
#                |                    v                       |                             |
#                |             +-------------+                |                             |
#                `------------>| Terminated  |<---------------+-----------------------------+
#                              +-------------+
#
        m.addTransition("Running:Stage-In",
                        "Terminated",
                        "terminate_token", self.do_terminate_stage_in)
        m.addTransition("Running:Stage-In",
                        "Failed",
                        "fail_token", self.do_stage_in_failed)
        m.addTransition("Running:Stage-In",
                        "Running:Instance-Starting",
                        "stage_in_completed_token", self.do_start_instance)
        m.addTransition("Running:Instance-Starting",
                        "Terminated",
                        "terminate_token", self.do_terminate_instance_starting)
        m.addTransition("Running:Instance-Starting",
                        "Failed",
                        "fail_token", self.do_instance_starting_failed)
        m.addTransition("Running:Instance-Starting",
                        "Running:Executing",
                        "instance_started_token", self.do_execute_task)
        m.addTransition("Running:Executing",
                        "Terminated",
                        "terminate_token", self.do_terminate_execution)
        m.addTransition("Running:Executing",
                        "Failed",
                        "fail_token", self.do_execution_failed)
        m.addTransition("Running:Executing",
                        "Running:Stage-Out",
                        "execution_finished_token", self.do_stage_out)
        m.addTransition("Running:Stage-Out",
                        "Failed",
                        "fail_token", self.do_stage_out_failed)
        m.addTransition("Running:Stage-Out",
                        "Terminated",
                        "terminate_token", self.do_terminate_stage_out)
        #
        # +-----------+ stageout +-----------+
        # |  Running  |--------->|  Finished |
        # | Stage-Out | complete |           |
        # +-----------+          +-----------+
        #
        #
        m.addTransition("Running:Stage-Out",
                        "Finished",
                        "stage_out_completed_token", self.do_task_finished)
        self.fsm = m

    def ID(self):
        """Return the ID for this task."""
        return self._id

    def state(self):
        """get the current state of the task."""
        return self.fsm.getCurrentState()

    # transition trigger methods
    def failed(self, reason):
        """the task has failed, reason should be a twisted.python.failure.Failure."""
        return self.fsm.consume("fail_token", reason)
    def terminate(self, reason=None):
        """user requests the termination."""
        return self.fsm.consume("terminate_token", reason)

    def confirm(self):
        """user confirmed the task"""
        return self.fsm.consume("confirm_token")
    def start(self):
        """initiate the starting of the task."""
        return self.fsm.consume("start_token")
    def execute(self):
        """triggers the execution of the task."""
        return self.fsm.consume("execute_task_token")

    # FSM transitions
    def do_confirmed(self, *args, **kw):
        pass
    def do_terminate_pending_reserved(self, reason, *args, **kw):
        pass
    def do_terminate_pending_confirmed(self, reason, *args, **kw):
        pass
    def do_stage_in(self, *args, **kw):
        # this method must be asynchronous
        # addCallback(self.stage_in_completed).addErrback(self.failed)
        # pre-cond: task description and non-file resources available
        # post-cond: state == Running:Stage-In
        pass
    def do_terminate_stage_in(self, reason, *args, **kw):
        # terminate the stage-in process, must not fail
        pass
    def do_stage_in_failed(self, *args, **kw):
        # handle the case, that the staging failed
        pass
    def do_start_instance(self, *args, **kw):
        # all files are staged in, so trigger the start of the instance
        # addCallback(self.instance_started).addErrback(self.failed)
        pass
    def do_terminate_instance_starting(self, reason, *args, **kw):
        pass
    def do_instance_starting_failed(self, reason, *args, **kw):
        # handle a failed instance start attempt
        pass
    def do_execute_task(self, *args, **kw):
        # pre-cond. instance available
        # post-cond. jsdl sent to instance
        pass
    def do_terminate_execution(self, reason, *args, **kw):
        # terminate the execution within the instance
        pass
    def do_execution_failed(self, reason, *args, **kw):
        # the task execution failed
        pass
    def do_stage_out(self, *args, **kw):
        # task has finished its execution,
        # instance has been shut down, stage out the data
        pass
    def do_stage_out_failed(self, reason, *args, **kw):
        # stage out process failed, so handle that
        pass
    def do_terminate_stage_out(self, *args, **kw):
        # user requested the termination of this task
        pass
    def do_task_finished(self):
        # pre-cond: stage-out is complete
        pass

    # callbacks, that will trigger FSM transitions
    def filesRetrieved(self):
        self.fsm.consume("files-retrieved")

    def prepare(self):
        return self.fsm.consume("prepare")

    def startInstance(self):
        return self.fsm.consume("start-instance")

    def instanceAvailable(self):
        self.fsm.consume("instance-available")

    def kill(self, signal=15):
        log.debug("TODO: send kill signal to task?")
        return self.failed(TaskError("killed"))

    def execute(self):
        log.debug("executing %s" % self.ID())
        return self.fsm.consume("execute")

    def finished(self, exitcode=0):
        return self.fsm.consume("finished", exitcode)

    # FSM callbacks
    def do_failed(self, reason):
        self.endTime = time.time()
        self.failReason = reason
        
        def instStopped(result):
            if isinstance(result, failure.Failure):
                log.fatal("stopping backend instance failed: %s" % result)
            else:
                log.info("backend stopped.")
            return self
        if self.inst.keep_running:
            log.debug("keeping the instance alive")
            return defer.succeed(self).addBoth(instStopped)
        else:
            return self.inst.stop().addBoth(instStopped)

    def do_prepare(self):
        return self.mgr.prepareTask(self)

    def do_pending(self):
        log.info("files for task have been retrieved")

    def do_startInstance(self):
        d = self.inst.start()
        def _s(arg):
            self.instanceAvailable()
            return self
        def _f(err):
            log.error("starting of my instance failed %s" % (err))
            return err
        d.addCallback(_s).addErrback(_f)
        return d

    def do_instanceAvailable(self):
        log.debug("my instance has been started")
        self.mgr.taskReady(self)

    def do_execute(self):
        self.startTime = time.time()
        log.info("executing task %s" % (self.ID()))
        self.inst.protocol.executeTask(task=self)

    def do_finished(self, exitcode):
        self.endTime = time.time()
        self.exitCode = exitcode
        def _s(result):
            self.mgr.taskFinished(self)
            return self
        if self.inst.keep_running:
            log.debug("keeping the instance alive")
            return defer.succeed(self).addBoth(_s)
        else:
            return self.inst.stop().addBoth(_s)
        
class TaskManager:
    """The task-manager.

    Through this class every known task can be controlled:
	- create new tasks

    """
    def __init__(self, inst_mgr, spool):
        """Initialize the TaskManager."""
        self.tasks = {}
        self.mtx = threading.RLock()
        self.instanceManager = inst_mgr
        self.spool = spool
        self.observers = [] # they are called when a new task has been created

    def notify(self, task, event):
        for observer, args, kw in self.observers:
            reactor.callLater(0.5, observer, task, event, *args, **kw)

    def addObserver(self, observer, *args, **kw):
        self.observers.append( (observer, args, kw) )

    def newTask(self, document):
        """Returns a new task."""
        from xbe.util.uuid import uuid
        self.mtx.acquire()

        task = Task(uuid(), self, document)

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

    def prepareTask(self, task):
        log.debug("starting preparation of task %s" % (task.ID(),))
        from xbe.xml import xsdl

        inst_desc = task.document.find("./"+xsdl.XSDL("InstanceDefinition"))

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

    def taskFailed(self, task):
        """Called when a task has failed somehow."""
        self.notify(task, "taskFailed")

    def taskReady(self, task):
        """Called when a task says, that it's ready."""
        self.notify(task, "taskReady")

    def taskFinished(self, task):
        """Called when a task finished."""
        self.notify(task, "taskFinished")

    def createSpool(self, _id, doSanityChecks=False):
        """Creates the spool-directory for a new task (using _id).

        The spool looks something like that: <spool>/UUID(task)/

        doSanityChecks -- some small tests to prohibit possible security breachs:
	    * result path is subdirectory of spool
	    * result path is not a symlink

        The spool directory is used to all necessary information about an instance:
	    * kernel, root, swap, additional images
	    * persistent configuration
	    * access and security stuff

        """
        import os, os.path
        
        path = os.path.normpath(os.path.join(self.spool, _id))
        if doSanityChecks:
            # perform small santiy checks
            if not path.startswith(self.spool):
                log.error("creation of spool directory (%s) failed:"+
                          " does not start with spool (%s)" % (path, self.spool))
                raise SecurityError("sanity check of spool directory failed:" +
                                    " not within spool")
            try:
                import stat
                if stat.S_ISLNK(os.lstat(path)[stat.ST_MODE]):
                    log.error("possible security breach: %s is a symlink" % path)
                    raise SecurityError("possible security breach: %s is a symlink" % path)
            except: pass
            if os.path.exists(path):
                log.error("new spool directory (%s) does already exist" +
                          " that should never happen!" % path)
                raise SecurityError("spool directory does already exist: %s" % path)

        # create the directory structure
        try:
            os.makedirs(path)
        except os.error, e:
            log.error("could not create spool directory: %s: %s" % (path, e))
            raise InstanceError("could not create spool directory: %s: %s" % (path,e))
        return path

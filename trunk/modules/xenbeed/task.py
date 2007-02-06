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

from xenbeed.exceptions import *
from xenbeed import util
from xenbeed import fsm

from twisted.internet import reactor

class TaskError(XenBeeException):
    pass

class Task(object):
    def __init__(self, ID, mgr, doc):
        """Initialize a new task."""
        self._id = ID
        self._tstamp = time.time()
        self.mgr = mgr
        self.document = doc
        self.inst = None
        self.instanceWaiter = None # defer activated, when the backend instance is available

        # build FSM
        m = fsm.FSM()
        m.newState("failed")
        m.newState("created")
        m.newState("preparing")
        m.newState("pending")
        m.newState("instance_starting")
        m.newState("instance_available")
        m.newState("running")
        m.newState("finished")

        for s in filter(lambda x: x != "failed", m.states()):
            m.addTransition(s, "failed", "failed", self.do_failed)
        m.addTransition("created", "preparing", "prepare", self.do_prepare)
        m.addTransition("preparing", "pending", "files-retrieved", self.do_pending)
        m.addTransition("pending", "instance_starting", "start-instance", self.do_startInstance)
        m.addTransition("instance_starting", "instance_available", "instance-available", self.do_instanceAvailable)
        m.addTransition("instance_available", "running", "execute", self.do_execute)
        m.addTransition("running", "finished", "finished", self.do_finished)
        
        m.setStartState("created")
        self.fsm = m

    def ID(self):
        """Return the ID for this task."""
        return self._id

    def state(self):
        return self.fsm.getCurrentState()

    def failed(self, extra_msg):
        self.fsm.consume("failed", extra_msg)

    def filesRetrieved(self):
        self.fsm.consume("files-retrieved")

    def prepare(self):
        return self.fsm.consume("prepare")

    def startInstance(self):
        return self.fsm.consume("start-instance")

    def instanceAvailable(self):
        self.fsm.consume("instance-available")

    def execute(self):
        return self.fsm.consume("execute")

    # FSM callbacks
    def do_failed(self, msg):
        self.extra_msg = msg
        self.mgr.taskFailed(self)

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
            log.err("instance could not be started: %s" % (err.getErrorMessage()))
            self.failed("instance could not be started: %s" % (err.getErrorMessage()))
            return err
        return d

    def do_instanceAvailable(self):
        self.mgr.taskReady(self)

    def do_execute(self):
        self.inst.protocol.executeTask(task=self)

    def do_finished(self):
        pass
        
class TaskManager:
    """The task-manager.

    Through this class every known task can be controlled:
	- create new tasks

    """
    def __init__(self, inst_mgr, base_path="/srv/xen-images/xenbee"):
        """Initialize the TaskManager."""
        self.tasks = {}
        self.mtx = threading.RLock()
        self.instanceManager = inst_mgr
        self.base_path = base_path
        self.observers = [] # they are called when a new task has been created

    def notify(self, task, event):
        for observer, args, kw in self.observers:
            reactor.callLater(0.5, observer, task, event, *args, **kw)

    def addObserver(self, observer, *args, **kw):
        self.observers.append( (observer, args, kw) )

    def newTask(self, document):
        """Returns a new task."""
        from xenbeed.uuid import uuid
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
        log.debug("starting preparation of %s" % (task.ID(),))
        import isdl

	# boot block
        imgDef = task.document.find(".//"+isdl.Tag("ImageDefinition", isdl.ISDL_NS))
	boot = imgDef.find(isdl.Tag("Boot", isdl.ISDL_NS))
	files = {}
	files["kernel"] = boot.find(".//"+isdl.Tag("Kernel")+
                                    "/"+isdl.Tag("URI")).text.strip()
	files["initrd"] = boot.find(".//"+isdl.Tag("Initrd")+
                                    "/"+isdl.Tag("URI")).text.strip()

	# image block
	images = imgDef.find(isdl.Tag("Images"))

	bootImage = images.find(isdl.Tag("BootImage"))
	files["root"] = bootImage.find(".//"+isdl.Tag("Source")+
                                       "/"+isdl.Tag("URI")).text.strip()

	log.debug(files)

        # create spool for task and instance and add files
        task.spool = self.createSpool(task.ID())
        inst = self.instanceManager.newInstance(task.spool)

        task.inst = inst
        inst.task = task

        d = inst.addFiles(files)
        def _s(arg):
            task.filesRetrieved()
            return task
        def _f(err):
            task.failed("file retrieval for task %s failed %s" %
                        (task.ID(), str(err.getTraceback())))
            return err
        d.addCallbacks(_s, _f)
        return d

    def taskFailed(self, task):
        """Called when a task has failed somehow."""
        self.notify(task, "taskFailed")

    def taskReady(self, task):
        """Called when a task says, that it's ready."""
        self.notify(task, "taskReady")

    def instanceAvailableForTask(self, task):
        """Called when the instance is available for the task."""
        task.instanceAvailable()
        self.notify(task, "instanceAvailable")

    def createSpool(self, _id, doSanityChecks=False):
        """Creates the spool-directory for a new task (using _id).

        The spool looks something like that: <base_path>/UUID(task)/

        doSanityChecks -- some small tests to prohibit possible security breachs:
	    * result path is subdirectory of base-path
	    * result path is not a symlink

        The spool directory is used to all necessary information about an instance:
	    * kernel, root, swap, additional images
	    * persistent configuration
	    * access and security stuff

        """
        import os, os.path
        
        path = os.path.normpath(os.path.join(self.base_path, _id))
        if doSanityChecks:
            # perform small santiy checks
            if not path.startswith(self.base_path):
                log.error("creation of spool directory (%s) failed:"+
                          " does not start with base_path (%s)" % (path, self.base_path))
                raise SecurityError("sanity check of spool directory failed:" +
                                    " not within base_path")
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

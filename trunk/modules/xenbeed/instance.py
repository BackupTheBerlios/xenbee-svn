"""
The XenBEE instance module (server side)

contains:
    InstanceManager:
	used to create new instances
	manages all currently available instances
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

import logging, os, os.path, time
import threading
log = logging.getLogger(__name__)

try:
    from traceback import format_exc as format_exception
except:
    from traceback import format_exception

from xenbeed.exceptions import *
from xenbeed.backend import backend
from xenbeed import util

from twisted.internet import reactor, threads, task, defer

class InstanceError(XenBeeException):
    pass

class Instance:
    def __init__(self, config, spool, mgr):
        """Initialize a new instance.

        config -- an InstanceConfig object that holds all necessary
        information about the instance.

        Requirement:
	    config.name must be a UUID.

        """

        # check if the instance name is a UUID
        # example: 85a21198-89db-11db-a9dc-d3d26ec3b24a
        import re
        uuid_pattern = r"^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$"
        p = re.compile(uuid_pattern)
        if not p.match(config.getInstanceName()):
            raise InstanceError("instance name is not a UUID: %s" % config.getInstanceName())
        self.config = config

        self.state = "created"
        self.spool = spool
        self.backend_id = -1
	self.mgr = mgr
        self.startTime = 0

    def __del__(self):
        log.debug("deleting instance")

    def uuid(self):
        """Return the UUID for this instance.

        This uuid does not have anything in common with a possible
        backend-uuid.

        currently the same as self.config.getInstanceName()

        """
        return self.config.getInstanceName()

    def ID(self):
        return self.uuid()

    def getName(self):
        """Return the instance name.

        same as self.config.getInstanceName()

        """
        return self.config.getInstanceName()

    def getConfig(self):
        """Return the underlying config."""
        return self.config

    def getBackendID(self):
        return self.backend_id

    def setBackendID(self, b_id):
        self.backend_id = b_id

    def addFile(self, uri, logical_name, copy=True):
        """retrieves the uri and stores it as logical_name within the spool."""
        dst = os.path.join(self.getSpool(), logical_name)
        if os.access(dst, os.F_OK):
            log.error("a file with the logical name '%s' does already exist." % logical_name)
            raise InstanceError("logical file '%s' already exists." % logical)

        from xenbeed.staging import DataStager
        try:
            ds = DataStager(uri, dst)
            ds.perform(asynchronous=False)
        except Exception, e:
            log.error("could not put file from: %s into spool: %s" % (uri, str(e)))
            raise InstanceError("could not retrieve %s: %s" % (uri, str(e)))
        return dst

    def addFiles(self, mapping={}, **kwords):
        """Add several files to this instance.

        The 'key' is the logical filename under which the files are stored.
        The 'values' are the files to retrieve.

        Example:
	    addFiles(kernel='file:///boot/vmlinuz',
		disk1='http://www.example.com/instance/test.img')

	    will copy the files '/boot/vmlinuz' (local) and '/instance/test.img'
	    (from www.example.com) to the spool directory as 'kernel' and 'disk1'.

        """
        logical_files = {}
        mapping.update(kwords)

        fileList = [(uri, self.getFullPath(name)) for name,uri in mapping.iteritems()]

        from xenbeed.staging import FileSetRetriever
        retriever = FileSetRetriever(fileList)

        d = retriever.perform()
        def __success(*args):
            log.info("successfully retrieved all files for: "+self.getName())
            self.state = "start-pending"
            return True
        def __fail(err):
            self.state = "failed"
            log.error("Retrieval failed: "+err.getTraceback())
            return err
        d.addCallbacks(__success, __fail)
        return d

    def getFullPath(self, logical_name):
        return os.path.join(self.getSpool(), logical_name)

    def getSpool(self):
        """Return the spool directory."""
        return self.spool

    def getBackendState(self):
        """Return the backend state of this instance.

        see: xenbeed.backend.status

        """
        return backend.getStatus(self)

    def getBackendInfo(self):
        """Return all information known about the backend instance."""
        return backend.getInfo(self)

    def stop(self):
        """Stop the instance."""
        if self.state == "started":
            d = threads.deferToThread(backend.shutdownInstance, self)
            def _s(arg):
                self.state = "stopped"
                self.mgr.removeInstance(self)
            d.addCallback(_s)
        else:
            raise InstanceError(getName()+" not yet started!")
        return d

    def cleanUp(self):
        """Removes all data belonging to this instance."""

        # check backend state
        backend_state = backend.getStatus(self)
        if backend_state in (backend.status.BE_INSTANCE_NOSTATE,
                             backend.status.BE_INSTANCE_SHUTOFF,
                             backend.status.BE_INSTANCE_CRASHED):
            util.removeDirCompletely(self.getSpool())

    def destroy(self):
        """Destroys the given instance.

        actions made:
	    * stop the instance
	    * removes the complete spool directory

        Warning: all data belonging to that instance are deleted, so be warned.

        essentially the same as:
	    stop()
	    cleanUp()

        """
        self.stop()
        self.cleanUp()

    def startable(self):
        return self.state == "start-pending"

    def __configure(self):
        self.config.setKernel(self.getFullPath("kernel"))
        self.config.setInitrd(self.getFullPath("initrd"))
        self.config.setMac("00:16:3e:00:00:02")
        self.config.addDisk(self.getFullPath("root"), "sda1")
        self.config.addToKernelCommandLine("XBE_SERVER=%s:%d" % ( "xen-o-matic.itwm.fhrg.fraunhofer.de", 61613))
        self.config.addToKernelCommandLine("XBE_UUID=%s" % (self.getName(),))
    
    def start(self):
        """Starts a new backend instance."""
        # check if needed files are available
        # (kernel, initrd, disks, etc.)
        self.state = "starting"
        
        self.__configure()
        
        # use the backend to start
	def __started(backendId):
	    self.state = "started"
            self.setBackendID(backendId)
            self.startTime = time.time()
        def __failed(err):
            log.error("starting failed: " + err.getErrorMessage())
            self.state = "failed"
            return err
        return threads.deferToThread(backend.createInstance, self).addCallback(__started).addErrback(__failed)

class InstanceManager:
    """The instance-manager.

    Through this class every known instance can be controlled:
	- send data (messages) to the manager on the instance
	- handle received data
	- create a new one

    """
    def __init__(self, base_path):
        """Initialize the InstanceManager."""
        self.instances = {}
        self.base_path = base_path
        self.__iter__ = self.instances.itervalues

    def newInstance(self, spool):
        """Returns a new instance.

        This instance does not have any files assigned.

        """
        from xenbeed.config.xen import InstanceConfig
        from xenbeed.uuid import uuid
        icfg = InstanceConfig(uuid())

        try:
            inst = Instance(icfg, spool, self)
        except:
            log.error(format_exception())
            raise
	
        # remember the instance in our db
        self.instances[inst.uuid()] = inst
        return inst

    def removeInstance(self, inst):
        """Remove the instance 'inst' from the manager.

        It is assumed that the instance has been stopped/destroyed
        before.

        """
        inst.mgr = None
        self.instances.pop(inst.uuid())

    def lookupByID(self, ID):
        return self.lookupByUUID(ID)

    def lookupByUUID(self, uuid):
        """Return the instance for the given identifier.

        returns the instance object or None

        """
        return self.instances.get(uuid, None)

    def lookupByBackendID(self, backend_id):
        """Return the instance with the given backend id."""
        for inst in self.instances.values():
            if inst.getBackendID() == backend_id:
                return inst
        return None

    def _createSpoolDirectory(self, uuid, doSanityChecks=True):
        """Creates the spool-directory for a new task.

        The spool looks something like that: <base_path>/UUID(inst)/

        doSanityChecks -- some small tests to prohibit possible security breachs:
	    * result path is subdirectory of base-path
	    * result path is not a symlink

        The spool directory is used to all necessary information about an instance:
	    * kernel, root, swap, additional images
	    * persistent configuration
	    * access and security stuff

        """
        path = os.path.normpath(os.path.join(self.base_path,
                                             uuid))
        if doSanityChecks:
            # perform small santiy checks
            if not path.startswith(self.base_path):
                log.error("creation of spool directory (%s) failed: does not start with base_path (%s)" % (path, self.base_path))
                raise SecurityError("sanity check of spool directory failed: not within base_path")
            try:
                import stat
                if stat.S_ISLNK(os.lstat(path)[stat.ST_MODE]):
                    log.error("possible security breach: %s is a symlink" % path)
                    raise SecurityError("possible security breach: %s is a symlink" % path)
            except: pass
            if os.path.exists(path):
                log.error("new spool directory (%s) does already exist, that should never happen!" % path)
                raise SecurityError("spool directory does already exist: %s" % path)

        # create the directory structure
        try:
            os.makedirs(path)
        except os.error, e:
            log.error("could not create spool directory: %s: %s" % (path, e))
            raise InstanceError("could not create spool directory: %s: %s" % (path,e))
        return path

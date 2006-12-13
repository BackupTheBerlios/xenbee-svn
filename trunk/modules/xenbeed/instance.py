"""
The XenBEE instance module (server side)

contains:
      InstanceManager:
           used to create new instances
           manages all currently available instances
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

import os, os.path

from twisted.python import log
from traceback import format_exc as format_exception

from xenbeed.exceptions import *
from xenbeed import backend

class InstanceError(XenBeeException):
    pass

class Instance:
    def __init__(self, config):
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
        self.spool = None
        self.backend_id = -1

    def uuid(self):
        """Return the UUID for this instance.

        This uuid does not have anything in common with a possible
        backend-uuid.

        currently the same as self.config.getInstanceName()

        """
        return self.config.getInstanceName()

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

    def getSpool(self):
        """Return the spool directory."""
        return self.spool

    def stop(self):
        """Stop the instance."""
        if self.state == "started":
            backend.shutdownInstance(self)
        self.state = "stopped"

    def cleanUp(self):
        """Removes all data belonging to this instance."""

        # check backend state
        backend_state, state_name = backend.getStatus(self)
        
        
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

    def start(self):
        """Starts a new backend instance."""
        # check if needed files are available
        # (kernel, initrd, disks, etc.)

        # TODO: make this a separate thread/process:
        #       * better control if something goes wrong
        #       * maybe use "call in thread" from twisted
        # use the backend to start
        self.setBackendID(backend.createInstance(self))
        self.state = "started"

class InstanceManager:
    """The instance-manager.

    Through this class every known instance can be controlled:
         - send data (messages) to the manager on the instance
         - handle received data
         - create a new one
    """
    def __init__(self):
        """Initialize the InstanceManager."""
        self.instances = {}
        self.base_path = "/srv/xen-images/xenbee"  # TODO: make this a configurable global variable

    def _createSpoolDirectory(self, inst, doSanityChecks=True):
        """Creates the spool-directory for a new instance.

        The spool looks something like that: <base-path>/UUID(inst)/

        inst -- the instance for which to create the directory
        doSanityChecks -- some small tests to prohibit possible security breachs:
              * result path is subdirectory of base-path
              * result path is not a symlink

        The spool directory is used to all necessary information about an instance:
              * kernel, root, swap, additional images
              * persistent configuration
              * access and security stuff

        """
        spool_path = inst.uuid()
        path = os.path.join(self.base_path, spool_path)
        path = os.path.normpath(path)

        if doSanityChecks:
            # perform small santiy checks
            if not path.startswith(self.base_path):
                log.err("creation of spool directory (%s) failed: does not start with base_path (%s)" % (path, self.base_path))
                raise SecurityError("sanity check of spool directory failed: not within base_path")
            try:
                import stat
                if stat.S_ISLNK(os.lstat(path)[stat.ST_MODE]):
                    log.err("possible security breach: %s is a symlink" % path)
                    raise SecurityError("possible security breach: %s is a symlink" % path)
            except: pass
            if os.path.exists(path):
                log.err("new spool directory (%s) does already exist, that should never happen!" % path)
                raise SecurityError("spool directory does already exist: %s" % path)

        # create the directory structure
        try:
            os.makedirs(path)
        except os.error, e:
            log.err("could not create spool directory: %s: %s" % (path, e))
            raise InstanceError("could not create spool directory: %s: %s" % (path,e))

        inst.spool = path
        return path

    def newInstance(self):
        """Returns a new instance.

        This instance does not have any files assigned.

        """
        from xenbeed.config.xen import InstanceConfig
        from xenbeed.uuid import uuid
        icfg = InstanceConfig(uuid())
        inst = Instance(icfg)

        try:
            self._createSpoolDirectory(inst)
        except:
            log.err(format_exception())
            raise

        # remember the instance in our db
        self.instances[inst.uuid()] = inst
        return inst

    def removeInstance(self, inst):
        """Remove the instance 'inst' from the manager.

        It is assumed that the instance has been stopped/destroyed
        before.
        
        """
        self.instances.pop(inst.uuid())

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

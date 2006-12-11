"""
The XenBEE instance module (server side)

contains:
      InstanceManager:
           used to create new instances
           manages all currently available instances
"""

import libvirt
import os, os.path

from xenbeed.config.xen import XenConfigGenerator
from xenbeed.exceptions import *
from twisted.python import log
from traceback import format_exc as format_exception

class InstanceError(XenBeeException):
    pass

class Instance:
    def __init__(self, config):
        self.config = config
        self.state = None
        self.spool = None

    def uuid(self):
        return self.config.getInstanceName()

    def getSpool(self):
        return self.spool
    
class InstanceManager:
    """The instance-manager.

    Through this class every known instance can be controlled:
         - send data (messages) to the manager on the instance
         - handle received data
         - create a new one
    """
    def __init__(self):
        # open a connection to the xen daemon
        try:
            self.xenConn = libvirt.open(None)
        except:
            log.err(format_exception())
            raise
        self.instances = {}

    def _createSpoolDirectory(self, inst, doSanityChecks=True):
        """Creates the spool-directory.

        The spool directory is used to all necessary information about an instance:
              * kernel, root, swap, additional images
              * persistent configuration
              * access and security stuff
        """
        base_path = "/srv/xen-images/xenbee"  # TODO: make this a configurable global configuration variable
        spool_path = inst.uuid()
        path = os.path.join(base_path, spool_path)
        path = os.path.normpath(path)

        if doSanityChecks:
            # perform small santiy checks
            if not os.path.startswith(base_path):
                log.err("creation of spool directory (%s) failed: does not start with base_path (%s)" % (path, base_path))
                raise SecurityError("sanity check of spool directory failed: not within base_path")
            import stat
            if stat.S_ISLNK(os.lstat(path)[stat.ST_MODE]):
                log.err("possible security breach: %s is a symlink" % path)
                raise SecurityError("possible security breach: %s is a symlink" % path)
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
        
        return inst

    def startInstance(self, inst):
        """Starts a new xen instance.

        inst - the instance to be instantiated (contains config etc.)
        """
        generator = XenConfigGenerator()
        try:
            cfg = generator.generate(config)
        except:
            log.err(format_exc())
            raise

        # check if needed files are available
        # (kernel, initrd, disks, etc.)
        

        # write current config to inst.spool/config
        try:
            cfg_path = os.path.join(inst.getSpool(), inst.uuid())
            cfg_file = open(cfg_path, "w")
            cfg_file.write(cfg)
            cfg_file.close()
        except:
            log.err("could not write current config: %s" % format_exception())
            raise


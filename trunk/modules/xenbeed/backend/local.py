"""The Local backend.

Implements the backend interface using no virtualization at all. The image is
mounted to some mountpoint after that the backend chroots to that point and
starts the backend instance daemon.
"""

__version__ = "$Rev: 34 $"
__author__ = "$Author: petry $"

import logging
log = logging.getLogger(__name__)

import commands, sys, os.path, threading
try:
    from traceback import format_exc as format_exception
except:
    from traceback import format_exception

from xenbeed.exceptions import *
from xenbeed.backend.status import *


class BackendInstance(object):
	
    def __init__(self, ident, inst):
        self.ident = ident
        self.instance = inst
        self.status = "created"

    def start(self):
        # start the xbeinstd
        pass

    def destroy(self):
        # destroy this instance
        pass

    def shutdown(self):
        # shut it down
        pass
    
    def ID(self):
        return self.ident
    
    def info(self):
        return None

class Backend(object):
    def __init__(self):
        self._lock = threading.RLock()
        self._instances = {} # mapping between instance names and backend instances.
        self._backendId = 0L # the global backend id counter

    def acquireLock(self):
        self._lock.acquire()

    def releaseLock(self):
        self._lock.release()

    def retrieveID(self, inst):
        """Retrieves the backend id for the given instance or -1."""
        try:
            return self._getBackendInstance(inst).ID()
        except:
            return -1

    def _getBackendInstance(self, name):
        return self._instances[name]

    def getStatus(self, inst):
        """Return the current status of 'inst'.

        returns a tuple of: (numeric status, readable form)

        see: http://libvirt.org/html/libvirt-libvirt.html

        Enum virDomainState {
            VIR_DOMAIN_NOSTATE = 0 : no state
            VIR_DOMAIN_RUNNING = 1 : the domain is running
            VIR_DOMAIN_BLOCKED = 2 : the domain is blocked on resource
            VIR_DOMAIN_PAUSED = 3 : the domain is paused by user
            VIR_DOMAIN_SHUTDOWN = 4 : the domain is being shut down
            VIR_DOMAIN_SHUTOFF = 5 : the domain is shut off
            VIR_DOMAIN_CRASHED = 6 : the domain is crashed
        }
    
        That are currently the same as in xenbeed.backend.status.
        
        """
        return self.getInfo(inst).state

    def getInfo(self, inst):
        try:
            self.acquireLock()
            domain = self._getBackendInstance(inst.getName())
            info = BackendDomainInfo(domain.info())
        finally:
            self.releaseLock()
        return info

    def _createInstance(self, inst):
        """Creates a new backend-instance.

        inst - an instance object (created by the InstanceManager)
        
        """
        log.info("attempting to create backend instance for: %s" % inst.getName())
        
        # check if another (or maybe this) instance is running with same name
        # (that should not happen!)
        if self.retrieveID(inst) >= 0:
            log.error("backend: another instance (or maybe this one?) is already known")
            raise InstanceCreationError("instance already known")

        # create the new BackendInstance and start it
        bi = BackendInstance(self._backendId)
        _instances[inst.getName()] = bi
        self._backendId += 1
        log.debug("created backend instance with id: %d" % (bi.ID(),))
        return bi.ID()

    def createInstance(self, inst):
        try:
            self.acquireLock()
            rv = self._createInstance(inst)
        finally:
            self.releaseLock()
        return rv

    def destroyInstance(self, inst):
        """Attempts to destroy the backend instance immediately."""
        bi = self._getBackendInstance(inst.getName())
        bi.destroy()

    def shutdownInstance(self, inst, wait=True):
        """Attempts to cleanly shut the backend instance down.
        
        WARNING: may not succeed, since the OS ignores the request.
        
        """
        log.info("attempting to shut instance %s down." % inst.getName())
        try:
            self.acquireLock()
            bi = self._getBackendInstance(inst)
            bi.shutdown()
        finally:
            self.releaseLock()
        return True


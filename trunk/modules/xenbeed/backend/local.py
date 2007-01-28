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

_lock = threading.RLock()
_instances = {} # mapping between instance names and backend instances.
_backendId = 0 # the global backend id counter

def acquireLock():
    global _lock
    if _lock: _lock.acquire()
def releaseLock():
    global _lock
    if _lock: _lock.release()

try:
    from traceback import format_exc as format_exception
except:
    from traceback import format_exception

from xenbeed.exceptions import *
from xenbeed.backend.status import *

__all__ = [ "createInstance",
            "retrieveID",
            "shutdownInstance",
            "destroyInstance",
            "getStatus",
            "getInfo" ]

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

def retrieveID(inst):
    """Retrieves the backend id for the given instance or -1."""
    try:
        return _getBackendInstance(inst).ID()
    except:
        return -1

def _getBackendInstance(name):
	return _instances[name]

def getStatus(inst):
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
    return getInfo(inst).state

def getInfo(inst):
    try:
        acquireLock()
        domain = _getBackendInstance(inst.getName())
        info = BackendDomainInfo(domain.info())
    finally:
        releaseLock()
    return info

def _createInstance(inst):
    """Creates a new backend-instance.

    inst - an instance object (created by the InstanceManager)

    """
    log.info("attempting to create backend instance for: %s" % inst.getName())

    # check if another (or maybe this) instance is running with same name
    # (that should not happen!)
    if retrieveID(inst) >= 0:
        log.error("backend: another instance (or maybe this one?) is already known to xen")
        raise InstanceCreationError("instance already known")

    # create the new BackendInstance and start it
    global _backendId
    bi = BackendInstance(_backendId)
    _instances[inst.getName()] = bi
    _backendId += 1
    log.debug("created backend instance with id: %d" % (bi.ID(),))
    return bi.ID()

def createInstance(inst):
    try:
	acquireLock()
	rv = _createInstance(inst)
    finally:
	releaseLock()
    return rv

def destroyInstance(inst):
    """Attempts to destroy the backend instance immediately.

    WARNING: the instance will be shutdown, so any programs running
	within the instance will be killed(!). From the xm
	man-page: it is equivalent to ripping the power cord.
    """
    bi = _getBackendInstance(inst.getName())
    bi.destroy()

def waitState(inst, states=(BE_INSTANCE_SHUTOFF), retries=5):
    """wait until the instance reached one of the given states.

    states -- a list of states (xenbeed.backend.status)
    retries -- the maximum number of retries

    returns True if the state has been reached, False otherwise.

    """
    from time import sleep
    for retry in xrange(retries):
	s = getStatus(inst)
        if s in states:
            log.debug("backend: reached state: %s" % (getStateName(s)))
            return s
        log.debug("backend: waiting for one of: %s currently in: %s" % (map(getStateName, states), getStateName(s)))
        sleep(0.5)
    return None

def shutdownInstance(inst, wait=True):
    """Attempts to cleanly shut the backend instance down.

    WARNING: may not succeed, since the OS ignores the request.

    """
    log.info("attempting to shut instance %s down." % inst.getName())
    try:
	acquireLock()
	bi = _getBackendInstance(inst)
	bi.shutdown()
    finally:
	releaseLock()
    return True


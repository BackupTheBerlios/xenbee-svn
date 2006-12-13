"""The Xen backend.

NOTE:

This backend partially uses the 'xm' command provided by xen and
partially functions provided by libvirt. The reason for that was, that
I could not create a new instance with libvirt, so if anybody can give
me a hint, I'll be very happy.

I have tried to use libvirt as best as I could.
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

import commands
import sys
import os.path
from traceback import format_exc as format_exception
from twisted.python import log

from xenbeed.config.xen import XenConfigGenerator
from xenbeed.exceptions import *
from xenbeed.backend.status import *

try:
    # try to use libvirt
    import libvirt
    libvirtConn = libvirt.open(None)

    # register an ErrorCallback
    def errHandler(ctx, error):
        # TODO: maybe log as debug?
        pass
    libvirt.registerErrorHandler(errHandler, None)
except:
    log.err("could not connect to xen backend!")
    raise

__all__ = [ "createInstance",
            "retrieveID",
            "shutdownInstance",
            "destroyInstance",
            "getStatus" ]

class BackendDomainInfo:
    """The python version of virDomainInfo.

       struct _virDomainInfo {
           unsigned char state: the running state, one of virDomainFlag
           unsigned long maxMem: the maximum memory in KBytes allowed
           unsigned long memory: the memory in KBytes used by the domain
           unsigned short nrVirtCpu: the number of virtual CPUs for the doma
           unsigned long long cpuTime: the CPU time used in nanoseconds
       }

    """
    
    def __init__(self, virDomainInfo):
        """Initializes from the list returned by virDomain.info()."""
        self.state, self.maxMem, self.memory, self.nrVirtCpu, self.cpuTime = virDomainInfo

def _runcmd(cmd, *args):
    """Executes the specified command on the xen backend, using 'xm'.

    WARNING: this function is exploitable using an injection mechanism
    
    TODO: find a way to escape correctly (re.escape includes
    double-backslashes not only for quotes)

    """
#    cmdline = "xm " + "'%s' " % re.escape(cmd) + " ".join(map(lambda x: "'%s'" % re.escape(str(x)), args))
    cmdline = "xm " + "'%s' " % cmd + " ".join(map(lambda x: "'%s'" % x, args))
    return commands.getstatusoutput(cmdline)

def _getDomain(inst):
    try:
        d = libvirtConn.lookupByName(inst.getName())
    except libvirt.libvirtError:
        raise BackendException("backend domain not found: %s" % inst.getName())
    return d

def retrieveID(inst):
    """Retrieves the backend id for the given instance."""
    try:
        return _getDomain(inst).ID()
    except:
        return -1

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
    try:
        domain = _getDomain(inst)
        info = BackendDomainInfo(domain.info())
        return info.state
    except:
        return BE_INSTANCE_NOSTATE

def createInstance(inst):
    """Creates a new backend-instance.

    inst - an instance object (created by the InstanceManager)

    """

    log.msg("attempting to create backend instance for: %s" % inst.getName())

    # check if another (or maybe this) instance is running with same name
    # (that should not happen!)
    if retrieveID(inst) >= 0:
        log.err("backend: another instance (or maybe this one?) is already known to xen")
        raise InstanceCreationError("instance already known")

    # build configuration
    generator = XenConfigGenerator() # TODO: create factory for 'backend'
    try:
        cfg = generator.generate(inst.config)
    except:
        log.err("backend: could not generate config: " + format_exception())
        raise
    
    # write current config to inst.spool/config
    try:
        cfg_path = os.path.join(inst.getSpool(), "config")
        cfg_file = open(cfg_path, "w")
        cfg_file.write(cfg)
        cfg_file.close()
    except:
        log.err("backend: could not write current config: %s" % format_exception())
        raise

    # dry-run and create instance
    (status, output) = _runcmd("dry-run", cfg_path)
    if status != 0:
        log.err("backend: could not execute dry-run: %d: %s" % (status, output))
        raise InstanceCreationError("dry-run failed: %d: %s" % (status, output))

    # TODO: decouple it using a thread/spawn whatever
    #    reason: the 'create' may hang due to some callbacks
    #            (e.g. network interfaces within the instance)
    (status, output) = _runcmd("create", cfg_path)
    if status != 0:
        log.err("backend: could not create backend instance: %d: %s" % (status, output))
        raise InstanceCreationError("create failed: %d, %s" % (status, output))
    backend_id = retrieveID(inst)
    inst.setBackendID(backend_id)
    return backend_id

def destroyInstance(inst):
    """Attempts to destroy the backend instance immediately.

    WARNING: the instance will be shutdown, so any programs running
             within the instance will be killed(!). From the xm
             man-page: it is equivalent to ripping the power cord.
    """
    domain = _getDomain(inst)
    domain.destroy()
    
#    (status, output) = _runcmd("destroy", inst.getBackendID())
#    if status != 0:
#        log.err("backend: could not destroy backend instance: %s" % output)
#        raise BackendException("destroy failed: %s" % output)

def waitState(inst, states=(BE_INSTANCE_SHUTOFF), retries=5):
    """wait until the instance reached one of the given states.

    states -- an iterable object of states (xenbeed.backend.status)
    retries -- the maximum number of retries

    """
    from time import sleep
    for retry in xrange(retries):
        if getStatus(inst) in states:
            log.msg("backend: reached state: %s" % (getStateName(getStatus(inst))))
            return True
        log.msg("backend: waiting for one of: %s" % map(getStateName, states), "currently in:", getStateName(getStatus(inst)))
        sleep(1)
    return False

def shutdownInstance(inst, wait=True):
    """Attempts to cleanly shut the backend instance down.

    WARNING: may not succeed, since the OS ignores the request.

    """
    domain = _getDomain(inst)
    domain.shutdown()

    if wait:
        result = waitState(inst, (BE_INSTANCE_NOSTATE,
                                  BE_INSTANCE_SHUTOFF,
                                  BE_INSTANCE_CRASHED))

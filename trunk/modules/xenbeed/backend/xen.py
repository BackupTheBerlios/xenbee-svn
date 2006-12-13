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

try:
    # try to use libvirt
    import libvirt
    libvirtConn = libvirt.open(None)

    # register an ErrorCallback
    def errHandler(ctx, error):
        print >>sys.stderr, error
    libvirtConn.registerErrorHandler(errHandler, None)
except:
    libvirtConn = None

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
        self.stateNames = [ "NOSTATE",
                            "RUNNING",
                            "BLOCKED",
                            "PAUSED",
                            "SHUTDOWN",
                            "SHUTOFF",
                            "CRASHED" ]

    def getStateName(self):
        """Return a human readable form of the state.

        NOSTATE = 0
        RUNNING = 1     the domain is running
        BLOCKED = 2     the domain is blocked on some resource
        PAUSED = 3      the domain is currently paused by the user
        SHUTDOWN = 4    the domain is shutting down
        SHUTOFF = 5     the domain is shut off
        CRASHED = 6     the domain has crashed
        
        """
        return self.stateNames[self.state]

def _runcmd(cmd, *args):
    """Executes the specified command on the xen backend, using 'xm'.

    WARNING: this function is exploitable using an injection mechanism
    
    TODO: find a way to escape correctly (re.escape includes
    double-backslashes not only for quotes)
    """
#    cmdline = "xm " + "'%s' " % re.escape(cmd) + " ".join(map(lambda x: "'%s'" % re.escape(str(x)), args))
    cmdline = "xm " + "'%s' " % cmd + " ".join(map(lambda x: "'%s'" % x, args))
    return commands.getstatusoutput(cmdline)

def retrieveID(inst):
    """Retrieves the backend id for the given instance."""
    if libvirtConn:
        try:
            domain = libvirtConn.lookupByName(inst.getName())
        except libvirt.libvirtError:
            return -1
        return domain.ID()
    else:
        (status, output) = _runcmd("domid", inst.getName())
        if status == 0:
            return int(output)
        else:
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

    """
    if libvirtConn:
        try:
            domain = libvirtConn.lookupByID(inst.getBackendID())
        except libvirt.libvirtError:
            log.err("backend: could not get domain: %d" % inst.getBackendID())
            raise BackendException("backend domain not found: %d" % inst.getBackendID())
        info = BackendDomainInfo(domain.info())
        return info.state, info.getStateName()
    else:
        raise BackendException("status retrieval currently not implemented")

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
        log.err("backend: could not execute dry-run: %s" % output)
        raise InstanceCreationError("dry-run failed: %s" % output)

    # TODO: decouple it using a thread/spawn whatever
    (status, output) = _runcmd("create", cfg_path)
    if status != 0:
        log.err("backend: could not create backend instance: %s" % output)
        raise InstanceCreationError("create failed: %s" % output)
    backend_id = retrieveID(inst)
    inst.setBackendID(backend_id)
    return backend_id

def destroyInstance(inst):
    """Attempts to destroy the backend instance immediately.

    WARNING: the instance will be shutdown, so any programs running
             within the instance will be killed(!). From the xm
             man-page: it is equivalent to ripping the power cord.
    """
    (status, output) = _runcmd("destroy", inst.getBackendID())
    if status != 0:
        log.err("backend: could not destroy backend instance: %s" % output)
        raise BackendException("destroy failed: %s" % output)

def shutdownInstance(inst):
    """Attempts to cleanly shut the backend instance down."""
    (status, output) = _runcmd("shutdown", inst.getBackendID())
    if status != 0:
        log.err("backend: could not shutdown backend instance: %s" % output)
        raise BackendException("destroy failed: %s" % output)

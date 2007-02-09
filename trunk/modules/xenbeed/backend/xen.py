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

import logging
log = logging.getLogger(__name__)

import commands, sys, os.path, threading

try:
    from traceback import format_exc as format_exception
except:
    from traceback import format_exception

from xenbeed.config.xen import XenConfigGenerator
from xenbeed.exceptions import *
from xenbeed.backend.status import *

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


class Backend(object):
    def __init__(self):
        self.lock = threading.RLock()
        try:
            # try to use libvirt
            import libvirt
            
            # register an ErrorCallback
            def errHandler(ctx, error):
                log.warn("backend error: %s" % (error,))
            libvirt.registerErrorHandler(errHandler, None)

            self.libvirtConn = libvirt.open(None)
            log.info("backend connected to libvirt")
        except:
            log.error("could not connect to xen backend!")
            raise

    def acquireLock(self):
        self.lock.acquire()

    def releaseLock(self):
        self.lock.release()

    def _runcmd(self, cmd, *args):
        """Executes the specified command on the xen backend, using 'xm'.

        WARNING: this function is exploitable using an injection mechanism

        TODO: find a way to escape correctly (re.escape includes
        double-backslashes not only for quotes)

        """
        #    cmdline = "xm " + "'%s' " % re.escape(cmd) + " ".join(map(lambda x: "'%s'" % re.escape(str(x)), args))
        cmdline = "xm " + "'%s' " % cmd + " ".join(map(lambda x: "'%s'" % x, args))
        return commands.getstatusoutput(cmdline)

    def _getDomainByName(self, inst):
        return self.libvirtConn.lookupByName(inst.getName())

    def _getDomain(self, inst):
        import libvirt.libvirtError
        try:
            if inst.backend_id in self.libvirtConn.listDomainsID():
                d = self._getDomainByName(inst)
            else:
                raise BackendException("backend domain not found: %s" % inst.getName())
        except libvirt.libvirtError, le:
            raise BackendException("backend domain not found: %s" % inst.getName(), le)
        return d

    def retrieveID(self, inst):
        """Retrieves the backend id for the given instance or -1."""
        try:
            return self._getDomainByName(inst).ID()
        except:
            return -1

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
        try:
            return self.getInfo(inst).state
        except:
            return BE_INSTANCE_NOSTATE

    def getInfo(self, inst):
        try:
            self.acquireLock()
            domain = self._getDomain(inst)
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
            log.error("backend: another instance (or maybe this one?) is already known to xen")
            raise InstanceCreationError("instance already known")

        # build configuration
        generator = XenConfigGenerator() # TODO: create factory for 'backend'
        try:
            cfg = generator.generate(inst.config)
        except:
            log.error("backend: could not generate config: " + format_exception())
            raise

        # write current config to inst.spool/config
        try:
            cfg_path = os.path.join(inst.getSpool(), "config")
            cfg_file = open(cfg_path, "w")
            cfg_file.write(cfg)
            cfg_file.close()
        except:
            log.error("backend: could not write current config: %s" % format_exception())
            raise

        # dry-run and create instance
        (status, output) = self._runcmd("dry-run", cfg_path)
        if status != 0:
            log.error("backend: could not execute dry-run: %d: %s" % (status, output))
            raise InstanceCreationError("dry-run failed: %d: %s" % (status, output))

        (status, output) = self._runcmd("create", cfg_path)
        if status != 0:
            log.error("backend: could not create backend instance: %d: %s" % (status, output))
            raise InstanceCreationError("create failed: %d, %s" % (status, output))
        backend_id = self.retrieveID(inst)
        log.debug("created backend instance with id: %d" % (backend_id,))
        return backend_id

    def createInstance(self, inst):
        try:
            self.acquireLock()
            rv = self._createInstance(inst)
        finally:
            self.releaseLock()
        return rv

    def destroyInstance(self, inst):
        """Attempts to destroy the backend instance immediately.

        WARNING: the instance will be shutdown, so any programs running
	within the instance will be killed(!). From the xm
	man-page: it is equivalent to ripping the power cord.
        """
        domain = self._getDomain(inst)
        domain.destroy()

    def waitState(self, inst, states=(BE_INSTANCE_SHUTOFF), timeout=60):
        """wait until the instance reached one of the given states.

        states -- a list of states (xenbeed.backend.status)
        timeout -- the maximum time that may elapse before an error is returned
        
        returns the state reached, or None otherwise.
        """
        import time
        end = int(time.time() + timeout)
        while True:
            s = self.getStatus(inst)
            if s in states:
                log.debug("backend: reached state: %s" % (getStateName(s)))
                return s
            if int(time.time()) >= end:
                break
            log.debug("backend: waiting for one of: %s currently in: %s" % (map(getStateName, states), getStateName(s)))
            time.sleep(1)
        return None

    def shutdownInstance(self, inst):
        """Attempts to cleanly shut the backend instance down.

        WARNING: may not succeed, since the OS ignores the request.
        """
        log.info("attempting to shut instance %s down." % inst.getName())
        try:
            self.acquireLock()
            domain = self._getDomain(inst)
            domain.shutdown()
        finally:
            self.releaseLock()
        if self.waitState(inst, (BE_INSTANCE_NOSTATE, BE_INSTANCE_SHUTOFF), timeout=60*2) is None:
            raise BackendException("shutdown timedout")
        return True

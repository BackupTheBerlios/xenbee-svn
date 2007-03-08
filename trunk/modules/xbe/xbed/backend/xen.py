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

import sys, os.path, threading, subprocess

try:
    from traceback import format_exc as format_exception
except:
    from traceback import format_exception

from xbe.xbed.config.xen import XenConfigGenerator
from xbe.xbed.backend.status import *
from xbe.util.exceptions import *

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
            libvirt.virInitialize()
            globals()["libvirt"] = libvirt
            
            # register an ErrorCallback
            def errHandler(ctx, error):
                # log.debug("backend error: %s" % (error,))
                pass
            libvirt.registerErrorHandler(errHandler, None)

            self.con = libvirt.open(None)
            log.info("backend connected to libvirt")
        except:
            log.error("could not connect to xen backend!")
            raise

    def acquireLock(self):
        self.lock.acquire()

    def releaseLock(self):
        self.lock.release()

    def _runcmd(self, cmd, *args):
        """Executes the specified command on the xen backend, using 'xm'."""
        argv = ['xm', cmd]
        argv.extend(args)
        p = subprocess.Popen(argv,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise ProcessError(p.returncode, "xm", stderr, stdout)
        
    def _getDomainByName(self, inst):
        return self.con.lookupByName(inst.id())

    def _getDomain(self, inst):
        try:
            if inst.getBackendID() in self.con.listDomainsID():
                d = self._getDomainByName(inst)
            else:
                raise BackendException("domain not found", inst.id())
        except Exception, e:
            raise BackendException("domain not found", inst.id(), e)
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

        That are currently the same as in xbe.xbed.backend.status.
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

    def getDefinedDomains(self):
        """Return a mapping from 'name' to id for all known domains."""
        try:
            domains = {}
            ids = self.con.listDomainsID()
            for domainID in ids:
                try:
                    name = self.con.lookupByID(domainID)
                except Exception, e:
                    # domain has disappeared?
                    pass
                else:
                    domains[name] = domainID
        finally:
            self.releaseLock()
        return domains

    def _createInstance(self, inst):
        """Creates a new backend-instance.
        
        inst - an instance object (created by the InstanceManager)
        
        """

        log.info("attempting to create backend instance for: %s" % inst.id())

        # check if another (or maybe this) instance is running with same name
        # (that should not happen!)
        if self.retrieveID(inst) >= 0:
            log.error("backend: another instance with that name is already known to xen")
            raise InstanceCreationError("instance already known", inst.id())

        # build configuration
        generator = XenConfigGenerator() # TODO: create factory for 'backend'
        try:
            cfg = generator.generate(inst.config())
        except:
            log.error("backend: could not generate config: " + format_exception())
            raise

        # write current config to inst.spool/config
        try:
            cfg_path = os.path.join(inst.spool(), "config")
            cfg_file = open(cfg_path, "w")
            cfg_file.write(cfg)
            cfg_file.close()
        except:
            log.error("backend: could not write current config: %s" % format_exception())
            raise

        # dry-run and create instance
        try:
            self._runcmd("dry-run", cfg_path)
        except ProcessError, e:
            log.error("backend: could not execute dry-run: %d: %s" % (e.returncode, e.stdout))
            raise InstanceCreationError("dry-run failed", inst.id(), e.returncode, e.stdout)

        try:
            self._runcmd("create", cfg_path)
        except ProcessError, e:
            log.error("backend: could not create backend instance: %d: %s" %
                      (e.returncode, e.stdout))
            raise InstanceCreationError("create failed", inst.id(), e.returncode, e.stdout)
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

        states -- a list of states (xbe.xbed.backend.status)
        timeout -- the maximum time that may elapse before an error is returned
        
        returns the state reached, or None otherwise.
        """
        log.debug("backend: waiting for one of: %s" % (map(getStateName, states)))

        import time
        end = int(time.time() + timeout)
        while True:
            s = self.getStatus(inst)
            if s in states:
                log.debug("backend: reached state: %s" % (getStateName(s)))
                return s
            if int(time.time()) >= end:
                break
            time.sleep(1)
        return None

    def shutdownInstance(self, inst, timeout=60*2):
        """Attempts to cleanly shut the backend instance down.

        WARNING: may not succeed, since the OS ignores the request.
        """
        log.info("attempting to shut instance %s down." % inst.id())
        try:
            self.acquireLock()
            domain = self._getDomain(inst)
            domain.shutdown()
        finally:
            self.releaseLock()
        if self.waitState(inst, (BE_INSTANCE_NOSTATE, BE_INSTANCE_SHUTOFF), timeout) == None:
            raise BackendException("shutdown timed out", inst.id())
        return True

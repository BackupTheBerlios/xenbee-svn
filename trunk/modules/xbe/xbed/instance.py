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

from xbe.util.exceptions import *
from xbe.xbed.backend import backend
from xbe.xbed.daemon import XBEDaemon
from xbe import util
from xbe.xml import xsdl

from twisted.internet import reactor, threads, task, defer
from twisted.python import failure
from urlparse import urlparse

class InstanceError(XenBeeException):
    pass

class InstanceTimedout(InstanceError):
    def __init__(self, msg, id):
        InstanceError.__init__(self, msg)
        self.id = id

class Instance(object):
    def __init__(self, config, spool, mgr):
        """Initialize a new instance.

        config -- an InstanceConfig object that holds all necessary
        information about the instance.

        Requirement:
	    config.name must be a UUID.

        """
        self.__state = "created"
        self.__config = config
        self.__spool = spool
        self.log = logging.getLogger("instance."+self.id())
	self.mgr = mgr
        
        # on instance-startup, a timer is created which results in notifying a failure
        # if the instance does not respond within __availableTimeout seconds
        self.__availableTimeout = 1*60

        self.__backend_id = -1
        self.__startTime = 0
        self.__last_message_tstamp = 0
        self.protocol = None # the protocol used to speak to the instance
        self.task = None

    def __del__(self):
        self.log.debug("deleting instance")

    def __repr__(self):
        return "<%(cls)s %(id)s in state %(state)s>" % {
            "cls": self.__class__.__name__,
            "id": self.id(),
            "state": self.state()
        }

    def uuid(self):
        """Return the UUID for this instance.

        This uuid does not have anything in common with a possible
        backend-uuid.

        currently the same as self.config.getInstanceName()

        """
        return self.config().getInstanceName()

    def id(self):
        return self.uuid()

    def state(self):
        return self.__state

    def config(self):
        return self.__config

    def spool(self):
        return self.__spool

    def getBackendID(self):
        return self.__backend_id

    def setBackendID(self, b_id):
        self.__backend_id = b_id

    def getBackendState(self):
        """Return the backend state of this instance.

        see: xbe.xbed.backend.status

        """
        return backend.getStatus(self)

    def getInfo(self):
        """Return all information known about the backend instance."""
        binfo = backend.getInfo(self)
        binfo.ips = getattr(self, 'ips', [])
        return binfo

    def stopped(self, result):
        self.state = "stopped"
        self.backend_id = -1
        return self

    def stop(self):
        """Stop the instance."""
        if self.state in ["started"]:
            return threads.deferToThread(backend.shutdownInstance,
                                         self).addCallback(self.stopped)
        else:
            return defer.succeed(self)

    def cleanUp(self):
        """Removes all data belonging to this instance."""
        return

    def destroy(self, *args, **kw):
        """Destroys the given instance."""
        return threads.deferToThread(backend.destroyInstance,
                                     self).addBoth(str).\
                                     addCallback(log.error).addCallback(self.stopped)

    def startable(self):
        return self.state == "start-pending"

    def start(self, timeout=None):
        """Starts a new backend instance.

        It returns a Deferred object, that is called back, when the
        instance has notified us, i.e. when the instance could be
        started correctly and is able to contact us.

        """
        try:
            self.__availableDefer
        except AttributeError:
            # no deferred currently active
            self.__availableDefer = defer.Deferred()
            self.state = "starting"
        else:
            return defer.fail(RuntimeError("instance already starting"))
        
        if timeout is None:
            timeout = self.__availableTimeout

        def __timeout_func(deferred):
            self.log.warn("timed out")
            deferred.errback(InstanceTimedout("instance timedout", self.id()))

        def __cancelTimer(arg, timer):
            # got signal from the backend instance
            timer.cancel()
            return arg
            
        self.__availableTimer = reactor.callLater(timeout,
                                                  __timeout_func,
                                                  self.__availableDefer)
        self.__availableDefer.addCallback(__cancelTimer, self.__availableTimer)
        
        # use the backend to start
	def __started(backendId):
	    self.state = "started"
            self.setBackendID(backendId)
            self.__startTime = time.time()
            return self
        def __failed(err):
            self.state = "failed"
            self.log.error("starting failed: " + err.getErrorMessage())
            self.__availableTimer.cancel()
            self.__availableDefer.errback(err)
            return self
        threads.deferToThread(backend.createInstance,
                              self).addCallback(__started).addErrback(__failed)
            
        return self.__availableDefer

    def available(self, inst_avail_msg, protocol):
        """Callback called when the 'real' instance has notified us."""
        self.ips = inst_avail_msg.ips()
        self.log.debug("now available at [%s]" % (", ".join(self.ips())))
        if not self.__availableDefer.called:
            self.protocol = protocol
            self.alive()
            self.__availableDefer.callback(self)
            del self.__availableDefer
            del self.__availableTimer

    def alive(self):
        self.__last_message_tstamp = time.time()

    def timeOfLastMessage(self):
        return self.__last_message_tstamp

from xbe.util import singleton
class InstanceManager(singleton.Singleton):
    """The instance-manager.

    Through this class every known instance can be controlled:
	- send data (messages) to the manager on the instance
	- handle received data
	- create a new one

    """
    def __init__(self, daemon):
        """Initialize the InstanceManager."""
        singleton.Singleton.__init__(self)
        self.instances = {}
        self.cache = daemon.cache
        self.__iter__ = self.instances.itervalues
        self.reaper = task.LoopingCall(self.reap, 5*60)
        self.reaper.start(1*60, now=False)

    def newInstance(self, spool):
        """Returns a new instance.

        This instance does not have any files assigned.

        """
        from xbe.xbed.config.xen import InstanceConfig
        from xbe.util.uuid import uuid
        icfg = InstanceConfig(uuid())

        try:
            inst = Instance(icfg, spool, self)
        except:
            log.error(format_exception())
            raise
	
        # remember the instance in our db
        self.instances[inst.uuid()] = inst
        return inst

    def reap(self, timeout):
        """Checks if an instance has been started but does not seem to
        be alive."""
        now = time.time()
        for inst in self.instances.values():
            if inst.state == "started":
                if (inst.timeOfLastMessage() + timeout) < now:
                    log.info("reaping stale instance %s" % inst.id())
                    inst.task.failed(
                        failure.Failure(
                        InstanceTimedout("instance seems dead", inst.id())))
            
    def removeInstance(self, inst):
        """Remove the instance 'inst' from the manager.

        It is assumed that the instance has been stopped/destroyed
        before.

        """
        inst.mgr = None
        self.instances.pop(inst.uuid())

    def lookupByID(self, id):
        return self.lookupByUUID(id)

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

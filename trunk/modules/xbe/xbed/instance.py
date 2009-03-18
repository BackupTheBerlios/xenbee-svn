# XenBEE is a software that provides execution of applications
# in self-contained virtual disk images on a remote host featuring
# the Xen hypervisor.
#
# Copyright (C) 2007 Alexander Petry <petry@itwm.fhg.de>.
# This file is part of XenBEE.

# XenBEE is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# XenBEE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA

"""
The XenBEE instance module (server side)

contains:
    InstanceManager:
	used to create new instances
	manages all currently available instances
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

import logging, os, os.path, time, threading
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
        self.__mtx = threading.RLock()
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

    def _setState(self, s):
        self.__mtx.acquire()
        try:
            self.__state = s
        finally:
            self.__mtx.release()

    def state(self):
        self.__mtx.acquire()
        try:
            rv = self.__state
        finally:
            self.__mtx.release()
        return rv

    def is_available(self):
        return self.state() == "started:available"
    def has_failed(self):
        return self.state() == "failed"
    def is_stopped(self):
        return self.state() == "stopped"
    def is_started(self):
        return self.state().startswith("started")
        
    def getBackendID(self):
        self.__mtx.acquire()
        try:
            rv = self.__backend_id
        finally:
            self.__mtx.release()
        return rv

    def setBackendID(self, b_id):
        self.__mtx.acquire()
        try:
            self.__backend_id = b_id
        finally:
            self.__mtx.release()

    def getBackendState(self):
        """Return the backend state of this instance.

        see: xbe.xbed.backend.status

        """
        self.__mtx.acquire()
        try:
            rv = backend.getStatus(self)
        finally:
            self.__mtx.release()
        return rv

    def getInfo(self):
        """Return all information known about the backend instance."""
        self.__mtx.acquire()
        try:
            rv = backend.getInfo(self)
        finally:
            self.__mtx.release()
        return rv

    def stop(self):
        """Stop the instance."""
        self.__mtx.acquire()
        try:
            if self.is_stopped():
                return True
            try:
                backend.shutdownInstance(self)
            except Exception, e:
                self.log.debug("shutdown failed, destroying: %s" % str(e))
                backend.destroyInstance(self)
            self._setState("stopped")
            self.setBackendID(-1)
        finally:
            self.__mtx.release()
        return True

    def start(self):
        """Starts a new backend instance."""
        self.__mtx.acquire()
        try:
            if self.is_started():
                return
            self.setBackendID(backend.createInstance(self))
            self.update_alive()
            self._setState("started")
        except:
            self._setState("failed")
            raise
        finally:
            self.__mtx.release()

    def life_sign(self, protocol, msg):
        """Callback called when the 'real' instance has sent us a life signal."""
        self.__mtx.acquire()
        try:
            self.log.debug("got life sign")
            self.__last_message_tstamp = time.time()
            self.protocol = protocol
            self._setState("started:available")
        finally:
            self.__mtx.release()

    def available(self, protocol):
        """Callback called when the 'real' instance has notified us."""
        self.__mtx.acquire()
        try:
            self.log.debug("now available")
            self._setState("started:available")
            self.protocol = protocol
        finally:
            self.__mtx.release()

    def update_alive(self):
        self.__mtx.acquire()
        try:
            self.__last_message_tstamp = time.time()
        finally:
            self.__mtx.release()

    def is_alive(self, consider_dead=5*60):
        return (self.timeOfLastMessage() + consider_dead) > time.time()

    def timeOfLastMessage(self):
        self.__mtx.acquire()
        try:
            rv = self.__last_message_tstamp
        finally:
            self.__mtx.release()
        return rv

from xbe.util.singleton import Singleton
from xbe.util.observer import Observable
class InstanceManager(Singleton, Observable):
    """The instance-manager.

    Through this class every known instance can be controlled:
	- send data (messages) to the manager on the instance
	- handle received data
	- create a new one

    """
    def __init__(self, daemon):
        """Initialize the InstanceManager."""
        Singleton.__init__(self)
        Observable.__init__(self)
        
        self.mtx = threading.RLock()
        self.instances = {}
        self.__iter__ = self.instances.itervalues
        self.reaper = task.LoopingCall(self.reap, 5*60)
        self.reaper.start(1*60, now=False)

    def newInstance(self, spool):
        """Returns a new instance.

        This instance does not have any files assigned.

        """
        from xbe.xbed.config.xen import InstanceConfig
        from xbe.util.uuid import uuid

        self.mtx.acquire()
        try:
            instance_name = "xbe-%s" % uuid()
            icfg = InstanceConfig(instance_name)
            
            try:
                inst = Instance(icfg, spool, self)
            except:
                log.error(format_exception())
                raise
            
            # remember the instance in our db
            self.instances[inst.uuid()] = inst
        finally:
            self.mtx.release()
        return inst

    def reap(self, timeout):
        """Checks if an instance has been started but does not seem to
        be alive."""
        now = time.time()
        for inst in self.instances.values():
            if inst.state().startswith("started"):
                if (inst.timeOfLastMessage() + timeout) < now:
                    log.info("reaping stale instance %s" % inst.id())
                    inst.task.signalExecutionFailed(
                        InstanceTimedout("instance seems dead", inst.id()))
            
    def removeInstance(self, inst):
        """Remove the instance 'inst' from the manager.

        It is assumed that the instance has been stopped/destroyed
        before.

        """
        self.mtx.acquire()
        try:
            inst.mgr = None
            self.instances.pop(inst.uuid())
        finally:
            self.mtx.release()

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

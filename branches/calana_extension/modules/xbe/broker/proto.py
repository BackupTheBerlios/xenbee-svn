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
The Xen Based Execution Environment protocol
"""

__version__ = "$Rev: 458 $"
__author__ = "$Author: petry $"

# system imports
import logging, re, time, threading
log = logging.getLogger(__name__)

from pprint import pprint, pformat
from lxml import etree

# twisted imports
from twisted.python import failure
from twisted.internet import defer, reactor, threads

# XBE imports
from xbe.stomp.proto import StompTransport
from xbe.proto import XenBEEProtocolFactory, XenBEEProtocol
from xbe.xml.namespaces import *
from xbe.xml import xsdl, message, protocol, errcode, jsdl
from xbe.concurrency import LockMgr

from xbe.broker.daemon import CalanaBrokerDaemon

##################################################
##
##################################################
class XenBEEClientProtocol(protocol.XMLProtocol):
    """The XBE client side protocol.

    This protocol is spoken between some client (user, script
    etc.). The protocol is based on XML
    """

    def __init__(self, client):
        protocol.XMLProtocol.__init__(self)
        self.client = client

    def connectionMade(self):
        log.debug("client %s has connected" % (self.client))

    def do_PingRequest(self, elem, *args, **kw):
        log.debug("pingRequest:")
        #transport = protocol.XMLTransport(StompTransport(stomp_protocol, "xenbee.daemons.1"))
        #transport.sendMessage(msg.as_xml())
        #transport.write(msg)

        #request = message.MessageBuilder.from_xml(elem.getroottree())
        #msg = message.PongResponse()
        msg = message.PingRequest()
        msg.destination = "/queue/xenbee.daemon.1"
        log.debug("sending: %s" % msg.as_xml())
        return msg

    def do_BookingRequest(self, elem, *args, **kw):
        msg = message.MessageBuilder.from_xml(elem.getroottree())
        log.debug("bookingRequest: ")
            
        def _success(uid):
            return message.Error(errcode.OK, uid)
        def _failure(reason):
            return message.Error(errcode.INTERNAL_SERVER_ERROR, reason.getErrorMessage())

##################################################
##
##################################################
class _XBEBrokerProtocol(XenBEEProtocol):
    def post_connect(self):
        pass

class XenBEEBrokerProtocolFactory(XenBEEProtocolFactory):
    protocol = _XBEBrokerProtocol

    def __init__(self, daemon, queue, topic, server_queue, user, password):
        log.debug("initializing broker protocol factory: id=%s,user=%s,server=%s" % (id, user, server_queue))

	XenBEEProtocolFactory.__init__(self, queue, user, password)
        self.daemon = daemon
        self.__topic = topic
        self.__server_queue = server_queue
        self.__protocolRemovalTimeout = 60
        self.__clientProtocols = {}
        self.__clientMutex = threading.RLock()

        #self.__instanceProtocols = {}
        #self.__instanceMutex = threading.RLock()

	#self.instanceManager = daemon.instanceManager
        #self.taskManager = daemon.taskManager
        #self.cache = daemon.cache
        self.cert = daemon.certificate
        self.ca_cert = daemon.ca_certificate

        from twisted.internet import task
        self.__cleanupLoop = task.LoopingCall(self.__cleanupOldProtocols)
        self.__cleanupLoop.start(5*60)

    def stompConnectionMade(self, stomp_prot):
        stomp_prot.subscribe(self.__topic)

    def dispatchToProtocol(self, transport, msg, domain, sourceType, sourceId=None):
        assert sourceType != None, "the source-type must not be None"

        if domain != "xenbee":
            raise ValueError("illegal domain: %s, expected 'calana'" % domain)

        if sourceId is None:
            raise ValueError(
                "illegal reply-to value, must be of the form: "+
                "/(queue|topic)/calana.[type].[id]")
        getattr(self, (sourceType.lower()+"Message"))(transport, msg, sourceId)

    def __messageHelper(self, id, msg, trnsprt, protocols, mtx, cls, *args, **kw):
        try:
            mtx.acquire()
            p = protocols.get(id)
            if p is None:
                p = cls(*args, **kw)
                p.factory = self
                protocols[id] = p
                p.makeConnection(trnsprt)
            p.timeOflastReceive = time.time()
        finally:
            mtx.release()
#        log.debug("got message for %r" % (p,))
        d = p.messageReceived(msg)
        if d is not None:
            # log sent answers
            d.addCallback(self.logCallback,
                          log.debug, "sending answer to %(client)s: %(result)s",
                          {"client": id})
    
            # finally log any error and consume them
            d.addErrback(self.logCallback,
                         log.error,
                         "sending message %(message)s to %(client)s failed: %(result)s",
                         { "client":id, "message": str(msg)})

    def logCallback(self, result, logfunc, fmt, dictionary):
        if result is not None:
            dictionary["result"] = str(result)
            logfunc(fmt % dictionary)

    def clientMessage(self, transport, msg, client):
        self.__messageHelper(client, msg, transport,
                             self.__clientProtocols,
                             self.__clientMutex,
                             protocol.SecureProtocol,
                             self.cert,
                             self.ca_cert,
                             self.certificateChecker,
                             XenBEEClientProtocol, client)

    def certificateChecker(self, certificate):
        return CalanaBrokerDaemon.getInstance().userDatabase.check_x509(certificate)

    # clean up registered protocols after some inactivity threshold
    def __cleanupOldProtocols(self):
        self.__cleanupHelper(self.__clientProtocols, self.__clientMutex)
        #self.__cleanupHelper(self.__instanceProtocols, self.__instanceMutex)

    def __cleanupHelper(self, protocols, mtx):
        try:
            mtx.acquire()
            tbr = [] # list of 'to be removed' items
            for id, p in protocols.iteritems():
                if (p.timeOflastReceive + self.__protocolRemovalTimeout) < time.time():
                    log.debug(
                        "removing registered protocol %s due to inactivity." % (id,))
                    tbr.append(id)
            map(protocols.pop, tbr)
        finally:
            mtx.release()

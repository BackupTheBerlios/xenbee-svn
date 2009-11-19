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

"""The protocol spoken by the commandline tool."""

import logging, sys, os, os.path

from pprint import pprint, pformat
log = logging.getLogger(__name__)

from xbe.stomp.proto import StompTransport
from xbe.xml import xsdl, message, protocol, errcode
from xbe.proto import XenBEEProtocolFactory, XenBEEProtocol
from lxml import etree
from xbe.xml.security import X509SecurityLayer, X509Certificate, SecurityError
from xbe.xml.namespaces import *

from twisted.internet import defer, reactor, task
from twisted.internet.protocol import BaseProtocol

class ClientXMLProtocol(protocol.XMLProtocol):
    protocolFactory = None
    protocol = None
    
    def __init__(self, protocolFactory=None, *protocolFactoryArgs, **protocolFactoryKwArgs):
        log.debug("initializing client protocol")

        if protocolFactory:
            self.protocolFactory = protocolFactory
            self.protocolFactoryArgs = protocolFactoryArgs
            self.protocolFactoryKwArgs = protocolFactoryKwArgs
    
    def connectionMade(self):
        """send initialization stuff"""
        log.debug("===== connectionMade")
        log.debug("client xml protocol connected")
        if self.protocolFactory is not None:
            self.protocol = self.protocolFactory(*self.protocolFactoryArgs,
                                                 **self.protocolFactoryKwArgs)
            try:
                factory = self.factory
            except AttributeError:
                pass
            else:
                self.protocol.factory = factory
            self.protocol.makeConnection(self)

    def do_CacheEntries(self, elem, *args, **kw):
        cache_entries = message.MessageBuilder.from_xml(elem.getroottree())
        if self.protocol is not None:
            self.protocol.cacheEntriesReceived(cache_entries)

    def do_StatusList(self, elem, *args, **kw):
        log.info("got status list")
        try:
            status_list = message.MessageBuilder.from_xml(elem.getroottree())
            if self.protocol is not None:
                self.protocol.statusListReceived(status_list)
        except Exception, e:
            log.warn("could not build status_list: %s", e)
        
    def do_ReservationResponse(self, elem, *args, **kw):
        response = message.MessageBuilder.from_xml(elem.getroottree())
        if self.protocol is not None:
            self.protocol.reservationResponseReceived(response)

    def do_Error(self, elem, *a, **kw):
        error = message.MessageBuilder.from_xml(elem.getroottree())
        if self.protocol is not None:
            self.protocol.errorReceived(error)

##calana extensions
    def do_PollResponse(self, elem, *a, **kw):
        log.info("ClientXMLProtocol::PollResponse")
        pollmsg = message.MessageBuilder.from_xml(elem.getroottree())
        log.info("ClientXMLProtocol::PollResponse (%s)" % pollmsg)
        if self.protocol is not None:
            self.protocol.pollResponseReceived(pollmsg)

    def do_PongWaitResponse(self, elem, *a, **kw):
        log.info("ClientXMLProtocol::Pong")
        pongmsg = message.MessageBuilder.from_xml(elem.getroottree())
        if self.protocol is not None:
            self.protocol.pongResponseReceived(pongmsg)

    def do_PongResponse(self, elem, *a, **kw):
        log.info("ClientXMLProtocol::Pong")
        pongmsg = message.MessageBuilder.from_xml(elem.getroottree())
        if self.protocol is not None:
            self.protocol.pongResponseReceived(pongmsg)

    def do_BookedResponse(self, elem, *a, **kw):
        log.info("Booked")
        bookingInformation = message.MessageBuilder.from_xml(elem.getroottree())
        if self.protocol is not None:
            self.protocol.bookedResponseReceived(bookingInformation)
        else:
            log.debug("===========Ups")
            
class BaseCommandLineProtocol(BaseProtocol):
    connected = 0

    def makeConnection(self, transport):
        log.debug("===== makeConnection")
        log.debug("making command line protocol connection")
        if not isinstance(transport, protocol.XMLProtocol):
            raise ValueError("sorry, but I expect a XMLProtocol")
        self.transport = transport   # it should be a XML protocol
        connected = 1
        log.debug("command line protcol connected")
        self.connectionMade()

    def connectionMade(self):
        log.debug("===== connectionMade")
        pass

    def reservationResponseReceived(self, reservationResponse):
        pass

    def statusListReceived(self, statusList):
        pass

    def cacheEntriesReceived(self, cache_entries):
        pass

    def errorReceived(self, error):
        pass

    def cacheFile(self, uri, type, desc):
        log.info("caching file: %s" % uri)
        msg = message.CacheFile(uri, type, desc)
        log.debug("sending: %s" % msg.as_xml())
        self.transport.sendMessage(msg.as_xml())

    def cacheRemove(self, uri):
	log.info("removing cache entry: %s" % uri)
        msg = message.CacheRemove(uri)
        self.transport.sendMessage(msg.as_xml())

    def requestTermination(self, ticket, remove_entry=False):
	log.info("terminating ticket: %s" % ticket)
        if remove_entry:
            log.warn("TODO: entry removal not yet implemented upon termination")
            remove_entry = False
        msg = message.TerminateRequest(ticket, remove_entry)
        log.debug("sending: %s" % msg.as_xml())
        self.transport.sendMessage(msg.as_xml())

    def requestStatus(self, ticket, remove_entry=False, execute_status_task=False):
        log.info("requesting status")
        msg = message.StatusRequest(ticket, remove_entry, execute_status_task)
        log.debug("sending: %s" % msg.as_xml())
        self.transport.sendMessage(msg.as_xml())

    def requestCacheList(self):
        log.info("requesting cache list")
        msg = message.ListCache()
        log.debug("sending: %s" % msg.as_xml())
        self.transport.sendMessage(msg.as_xml())

    def requestReservation(self):
	log.info("requesting a reservation") 
        msg = message.ReservationRequest()
        log.debug("sending: %s" % msg.as_xml())
        self.transport.sendMessage(msg.as_xml())

    def confirmReservation(self, ticket, jsdl, auto_start=True):
	log.info("confirming reservation: %s" % ticket)
        msg = message.ConfirmReservation(ticket, jsdl, auto_start)
        log.debug("sending: %s" % msg.as_xml())
        self.transport.sendMessage(msg.as_xml())

    def requestStart(self, ticket):
	log.info("requesting start of ticket: %s" % ticket)
        msg = message.StartRequest(ticket)
        log.debug("sending: %s" % msg.as_xml())
        self.transport.sendMessage(msg.as_xml())
        
## calana extensions
    def pollRequest(self, cmdname):
	log.info("BaseCommandLineProtocol::pollRequest")
        msg = message.PollRequest(cmdname)
        log.debug("sending: %s" % msg.as_xml())
        self.transport.sendMessage(msg.as_xml())

    def pingRequest(self):
	log.info("ping request of ticket: ")
        msg = message.PingRequest()
        log.debug("sending: %s" % msg.as_xml())
        self.transport.sendMessage(msg.as_xml())

    def pingRequestPoll(self):
	log.info("pingRequest poll: ")
        msg = message.PingRequestPoll()
        log.debug("sending: %s" % msg.as_xml())
        self.transport.sendMessage(msg.as_xml())

    def pongResponseReceived(self, pongmsg):
	log.info("====pongResponseReceived.")
        pass

    def bookingRequest(self):
	log.info("booking request of ticket: ")
        msg = message.BookingRequest()
        log.debug("sending: %s" % msg.as_xml())
        self.transport.sendMessage(msg.as_xml())

    def bookingRequestPoll(self):
	log.info("booking request of ticket: ")
        msg = message.BookingRequestPoll()
        log.debug("sending: %s" % msg.as_xml())
        self.transport.sendMessage(msg.as_xml())

class SimpleCommandLineProtocol(BaseCommandLineProtocol):
    def errorReceived(self, error):
        print >>sys.stderr, repr(error)

    def bookedResponseReceived(self, bookingInformation):
	log.info("====================SimpleCommandLineProtocol::bookedResponseReceived")
        #msg = message.ConfirmReservation(ticket, jsdl, auto_start)
        pass


class ClientProtocolFactory(XenBEEProtocolFactory):
    def __init__(self, id, stomp_user, stomp_pass,
                 certificate, ca_cert, server_queue,
                 protocolFactory=None,
                 protocolFactoryArgs=(),
                 protocolFactoryKwArgs={}):
        log.debug("initializing client protocol factory: id=%s,user=%s,server=%s" % (id, stomp_user, server_queue))
        XenBEEProtocolFactory.__init__(self,
#                                       "/queue/calana.client.%s" % (id),
                                       "/queue/xenbee.client.%s" % (id),
                                       stomp_user, stomp_pass)
        self.protocolFactory = protocolFactory
        self.protocolFactoryArgs = protocolFactoryArgs
        self.protocolFactoryKwArgs = protocolFactoryKwArgs

        self.client_id = id
        self.server_queue = server_queue
        self.cert = certificate
        self.ca_cert = ca_cert
	log.debug("client protocol factory initialized")
        
    def dispatchToProtocol(self, transport, msg, domain, sourceType, sourceId=None):
        d = defer.maybeDeferred(self.xml_protocol.messageReceived, msg)
        d.addErrback(log.error)

    def stompConnectionMade(self, stomp_protocol):
        log.debug("===== stompConnectionMade")
        log.debug("stomp connection established")
        try:
            self.xml_protocol
        except AttributeError:
            self.xml_protocol = \
                              protocol.SecureProtocol(self.cert,
                                                      self.ca_cert,
                                                      None,
                                                      self.protocolFactory,
                                                      *self.protocolFactoryArgs,
                                                      **self.protocolFactoryKwArgs)
            self.xml_protocol.factory = self
            self.xml_protocol.makeConnection(
                protocol.XMLTransport(StompTransport(stomp_protocol, self.server_queue)))
            self.xml_protocol.init_handshake()

if __name__ == "__main__":
    path = os.path.join(os.environ["HOME"], ".xbe", "cert")
    cert = X509Certificate.load_from_files(os.path.join(path, "user.pem"),
                                           os.path.join(path, "private", "user-key.pem"))
    ca_cert = X509Certificate.load_from_files("/root/xenbee/etc/CA/ca-cert.pem")

#    path = os.path.join(os.environ["HOME"], "tmp", "x.509")
#    cert = X509Certificate.load_from_files(os.path.join(path, "signer.pem"),
#                                           os.path.join(path, "signer_key.pem"))
#   ca_cert = X509Certificate.load_from_files("/root/xenbee/etc/CA/ca-cert.pem")
    
    f = ClientProtocolFactory(id="2",
                              stomp_user="test-user-1", stomp_pass="test-pass-1",
                              certificate=cert, ca_cert=ca_cert,
                              server_queue="/queue/xenbee.daemon.1",
                              protocolFactory=ClientXMLProtocol,
                              protocolFactoryArgs=(SimpleCommandLineProtocol,))
    reactor.connectTCP("localhost", 61613, f)
    reactor.run()

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
        if protocolFactory:
            self.protocolFactory = protocolFactory
            self.protocolFactoryArgs = protocolFactoryArgs
            self.protocolFactoryKwArgs = protocolFactoryKwArgs
    
    def connectionMade(self):
        """send initialization stuff"""
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
        try:
            status_list = message.MessageBuilder.from_xml(elem.getroottree())
        except Exception, e:
            log.warn("could not build status_list: %s", e)
        else:
            if self.protocol is not None:
                self.protocol.statusListReceived(status_list)
        
    def do_ReservationResponse(self, elem, *args, **kw):
        response = message.MessageBuilder.from_xml(elem.getroottree())
        if self.protocol is not None:
            self.protocol.reservationResponseReceived(response)

    def do_Error(self, elem, *a, **kw):
        error = message.MessageBuilder.from_xml(elem.getroottree())
        if self.protocol is not None:
            self.protocol.errorReceived(error)

class BaseCommandLineProtocol(BaseProtocol):
    connected = 0

    def makeConnection(self, transport):
        if not isinstance(transport, protocol.XMLProtocol):
            raise ValueError("sorry, but I expect a XMLProtocol")
        self.transport = transport   # it should be a XML protocol
        connected = 1
        log.debug("command line protcol connected")
        self.connectionMade()

    def connectionMade(self):
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
        msg = message.CacheFile(uri, type, desc)
        self.transport.sendMessage(msg.as_xml())

    def requestTermination(self, ticket, remove_entry=False):
        if remove_entry:
            log.warn("TODO: entry removal not yet implemented upon termination")
            remove_entry = False
        msg = message.TerminateRequest(ticket, remove_entry)
        self.transport.sendMessage(msg.as_xml())

    def requestStatus(self, ticket, remove_entry=False):
        msg = message.StatusRequest(ticket, remove_entry)
        self.transport.sendMessage(msg.as_xml())

    def requestCacheList(self):
        msg = message.ListCache()
        self.transport.sendMessage(msg.as_xml())

    def requestReservation(self):
        msg = message.ReservationRequest()
        self.transport.sendMessage(msg.as_xml())

    def confirmReservation(self, ticket, jsdl, auto_start=True):
        msg = message.ConfirmReservation(ticket, jsdl, auto_start)
        self.transport.sendMessage(msg.as_xml())

class SimpleCommandLineProtocol(BaseCommandLineProtocol):
    def errorReceived(self, error):
        print >>sys.stderr, repr(error)

class ClientProtocolFactory(XenBEEProtocolFactory):
    def __init__(self, id, stomp_user, stomp_pass,
                 certificate, ca_cert, server_queue,
                 protocolFactory=None,
                 protocolFactoryArgs=(),
                 protocolFactoryKwArgs={}):
        XenBEEProtocolFactory.__init__(self,
                                       "/queue/xenbee.client.%s" % (id),
                                       stomp_user, stomp_pass)
        self.protocolFactory = protocolFactory
        self.protocolFactoryArgs = protocolFactoryArgs
        self.protocolFactoryKwArgs = protocolFactoryKwArgs

        self.client_id = id
        self.server_queue = server_queue
        self.cert = certificate
        self.ca_cert = ca_cert
        
    def dispatchToProtocol(self, transport, msg, domain, sourceType, sourceId=None):
        d = defer.maybeDeferred(self.xml_protocol.messageReceived, msg)
        d.addErrback(log.error)

    def stompConnectionMade(self, stomp_protocol):
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

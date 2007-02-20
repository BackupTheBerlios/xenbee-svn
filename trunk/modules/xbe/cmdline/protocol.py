"""The protocol spoken by the commandline tool."""

import logging, sys, os, os.path
from pprint import pprint
log = logging.getLogger(__name__)

# log to stderr
logging.currentframe = lambda: sys._getframe(3)
_stderr = logging.StreamHandler(sys.stderr)
_stderr.setLevel(logging.DEBUG)
_stderr.setFormatter(logging.Formatter('%(name)s:%(lineno)d: %(levelname)-8s %(message)s'))
logging.getLogger().addHandler(_stderr)
logging.getLogger().setLevel(logging.DEBUG)

from xbe.stomp.proto import StompTransport
from xbe.xml import xsdl, message, protocol
from xbe.proto import XenBEEProtocolFactory, XenBEEProtocol
from lxml import etree
from xbe.xml.security import X509SecurityLayer, X509Certificate, SecurityError
from xbe.xml.namespaces import *

from twisted.internet import defer, reactor

class ClientXMLProtocol(protocol.XMLProtocol):
    def connectionMade(self):
        """send initialization stuff"""
        log.info("client protocol connected")
        msg = message.StatusRequest()
        self.sendMessage(msg.as_xml())
        msg = message.ListCache()
        self.sendMessage(msg.as_xml())

    def do_CacheEntries(self, elem, *args, **kw):
        cache_entries = message.MessageBuilder.from_xml(elem.getroottree())
        print "got cache entries:"
        pprint(cache_entries.entries())

    def do_StatusList(self, elem, *args, **kw):
        status_list = message.MessageBuilder.from_xml(elem.getroottree())
        print "got status list:"
        pprint(status_list.entries())
        

class ClientProtocol(XenBEEProtocol):
    def post_connect(self):
        # schedule timer and send CertificateRequest/LoginRequest...

        # notify the upper layer, that it may connect now
        self.factory.xml_protocol.makeConnection(
            protocol.XMLTransport(StompTransport(self, self.factory.server_queue)))
        self.factory.xml_protocol.init_handshake()

class ClientProtocolFactory(XenBEEProtocolFactory):
    protocol = ClientProtocol
    
    def __init__(self, id, certificate, ca_cert):
        XenBEEProtocolFactory.__init__(self, "/queue/xenbee.client.%s" % (id), "test-user-1")
        self.client_id = id
        self.server_queue = "/queue/xenbee.daemon"
        self.cert = certificate
        self.ca_cert = ca_cert
        self.xml_protocol = protocol.SecureProtocol(self.cert, self.ca_cert, ClientXMLProtocol)
        self.xml_protocol.factory = self

    def dispatchToProtocol(self, transport, msg, domain, sourceType, sourceId=None):
        if "/queue/%s.%s" % (domain, sourceType) != self.server_queue:
            raise RuntimeError("illegal source of message: %s" % (sourceType))
        if self.xml_protocol is None:
            self.xml_protocol.makeConnection(transport)
        d = defer.maybeDeferred(self.xml_protocol.messageReceived, msg)
        d.addErrback(log.error)

if __name__ == "__main__":
    path = os.path.join(os.environ["HOME"], ".xbe", "cert")
    cert = X509Certificate.load_from_files(os.path.join(path, "user.pem"),
                                           os.path.join(path, "private", "user-key.pem"))
    ca_cert = X509Certificate.load_from_files("/root/xenbee/etc/CA/ca-cert.pem")
    
    f = ClientProtocolFactory(id="2", certificate=cert, ca_cert=ca_cert)
    reactor.connectTCP("localhost", 61613, f)
    reactor.run()

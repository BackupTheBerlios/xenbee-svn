"""
The Xen Based Execution Environment XML Protocol
"""

import logging
log = logging.getLogger(__name__)

from pprint import pformat

from xbe.xml.namespaces import *
from xbe.xml import message, errcode
from xbe.xml.security import X509SecurityLayer, X509Certificate, SecurityError

from lxml import etree
from twisted.internet import defer, reactor
from twisted.python import failure

class StringTransport:
    def __init__(self, transport):
        self.__transport = transport

    def write(self, data):
        return self.__transport.write(str(data))

class XMLTransport(StringTransport):
    def __init__(self, transport):
        StringTransport.__init__(self, transport)

    def write(self, msg):
        if isinstance(msg, (etree._Element, etree._ElementTree)):
            msg = etree.tostring(msg, xml_declaration=True)
        elif isinstance(msg, message.Message):
            msg = msg.as_str()
        if msg is not None:
            StringTransport.write(self, msg)
        return None

class XMLProtocol(object):
    """The base class of all client-protocols that are used here."""

    def __init__(self):
        self.factory = None

        # a list of ({uri}localName) tuples that are
        # understood by the protocol
        self.__understood = []

    def makeConnection(self, transport):
        self.connected = 1
        self.transport = transport
        self.connectionMade()

    def connectionMade(self):
        pass
    
    def dispatch(self, elem, *args, **kw):
        method = getattr(self, "do_%s" % (decodeTag(elem.tag)[1]))
        return method(elem, *args, **kw)

    def addUnderstood(self, tag):
        if tag not in self.__understood:
            self.__understood.append(tag)

    def transformResultToMessage(self, result):
        log.debug("transforming result '%r'" % result)
        if result is None:
            # do not reply, so return None
            return None

        if isinstance(result, failure.Failure):
            log.warn("failure occured: %s\n%s" % (result.getErrorMessage(), result.getTraceback()))
            result = message.Error(errcode.INTERNAL_SERVER_ERROR,
                                   result.getErrorMessage())
        assert isinstance(result, message.Message), "attempted to transform strange result"

        # return the xml document
        return result.as_xml()

    def sendMessage(self, msg):
        if msg is not None:
            assert (isinstance(msg, (etree._Element, etree._ElementTree)),
                    "message to be sent must be XML")
            try:
                return self.transport.write(msg)
            except Exception, e:
                log.error("message sending failed: %s" % (e,))
        log.debug("nothing to answer...")

    def parse_and_validate(self, msg):
        if isinstance(msg, basestring):
            xml = etree.fromstring(msg)
        else:
            xml = msg
        # validate xml against schema
        log.warn("TODO: validate against XML-Schema")
        assert (isinstance(xml, (etree._Element, etree._ElementTree)))

        # build xbe.xml.message
        try:
            msg_obj = message.MessageBuilder.from_xml(xml)
        except Exception, e:
            log.warn("TODO: write builder for %s", e.message)
        return xml

    def messageReceived(self, msg):
        """Handle an incoming XML message.

        The message handling code works as follows:

             * a method is looked up according to the 'tag' of the root element
               or the first direct child that 
        """
        log.debug("got message: '%r'" % msg)
        d = defer.maybeDeferred(self._messageReceived, msg)
        d.addBoth(self.transformResultToMessage)
        d.addCallback(self.sendMessage)
        return d

    def _messageReceived(self, msg):
	"""Handle a received message."""
        return self.dispatch(self.parse_and_validate(msg))

    # some default xml-element handler
    #
    def do_Message(self, msg, *args, **kw):
        # handle a XBE-Message
        #
        # decompose into header and body
        hdr = msg.find(XBE("MessageHeader"))
        if hdr is not None:
            bod = msg.find(XBE("MessageBody"))
            if bod and len(bod):
                return self.dispatch(bod[0], *args, **kw)
            else:
                log.debug("got message with missing or empty body, ignoring it.")
        else:
            log.warn("Deprecation: messages must now contain Header and Body elements")
            return self.dispatch(msg[0], *args, **kw)

    def do_Error(self, err, *args, **kw):
        log.error("got error:\n%s" % (etree.tostring(err)))
        log.error("args: %s" % pformat(args))
        log.error("kw: %s" % pformat(kw))
        


class SecureXMLTransport(XMLTransport):
    def __init__(self, transport, securityLayer):
        XMLTransport.__init__(self, transport)
        self.securityLayer = securityLayer
        
    def write(self, msg):
        if isinstance(msg, message.Message):
            msg = msg.as_xml()
        _msg = self.securityLayer.sign(msg)[0]
        _msg = self.securityLayer.encrypt(_msg)
        return XMLTransport.write(self, _msg)

class SecureProtocol(XMLProtocol):
    protocol = None
    protocolFactory = None
    
    def __init__(self, cert, ca_cert, protocolFactory=None, *a, **kw):
        XMLProtocol.__init__(self)
        if protocolFactory:
            self.protocolFactory = protocolFactory
            self.protocolFactoryArgs = a
            self.protocolFactoryKwArgs = kw
        self.__cert = cert
        self.__ca_cert = ca_cert
        self.__state = "disconnected"

        # initialize the security layer
        self.securityLayer = X509SecurityLayer(self.__cert, # my own certificate
                                               None, # the other's certificate
                                               [self.__ca_cert])

    def connectionMade(self):
        self.__state = "establishing"
        self.__handshakeTimeout = reactor.callLater(5, self.__handshake_failed)

    def __handshake_failed(self):
        log.warn("Message Layer Security handshake *failed*")
        self.__state = "disconnected"
        
    def __handshake_complete(self):
        log.info("Message Layer Security established.")
        self.__state = "established"
        self.__handshakeTimeout.cancel()
        del self.__handshakeTimeout
        
        # instantiate the upper protocol
        if self.protocolFactory:
            log.info("attaching application layer")
            self.protocol = self.protocolFactory(*self.protocolFactoryArgs, **self.protocolFactoryKwArgs)
            try:
                factory = self.factory
            except AttributeError:
                pass
            else:
                self.protocol.factory = factory

            # connect it with a secure transport
            # (thus we act as a secure lower layer)
            self.protocol.makeConnection(SecureXMLTransport(self.transport, self.securityLayer))

    # handle security related messages
    def do_Message(self, msg):
        # decompose into header and body
        hdr = msg.find(XBE("MessageHeader"))
        bod = msg.find(XBE("MessageBody"))

        if hdr is None:
            log.error("ignoring illegal message: '%r'" % (etree.tostring(msg)))
            return

        if not bod or not len(bod):
            log.debug("got empty message, checking signature...")
            # we got just a MessageHeader, so validate at least that part
            try:
                self.securityLayer.validate(msg)
                if self.securityLayer.fully_established() and self.__state != "established":
                    self.__handshake_complete()
            except SecurityError, se:
                log.debug("got a message from not-validatable source: %s" % (" ".join(se.args)))
                return message.Error(errcode.UNAUTHORIZED)
            return
        
        if bod and len(bod):
            log.debug("dispatching %s" % bod[0].tag)
            return self.dispatch(bod[0], msg)
        else:
            return None

    def do_CipherData(self, cipherdata, msg):
        """handle ciphered data.

        decrypts the received data and validates it.
        """
        # decrypt the whole message and validate it
        try:
            real_msg = self.securityLayer.decrypt(msg)
        except Exception, e:
            from traceback import format_exc
            log.error("decyphering *failed*: %s\n%s" % (e, format_exc(e)))
            raise
        # validate the message
        try:
            real_msg = self.securityLayer.validate(real_msg)
        except SecurityError, se:
            return message.Error(errcode.UNAUTHORIZED)
        log.debug("received application data: %s" % real_msg.tag)
        try:
            rv = self.protocol.messageReceived(real_msg)
        except Exception, e:
            log.debug("handling of application data failed: %s", e)
        return rv
    
    def do_CertificateRequest(self, req, msg):
        """handle a CertificateRequest.

        simply sends a message with an empty body, but signs and
        includes the certificate.
        """
        try:
            self.securityLayer.validate(msg)
            if self.securityLayer.fully_established() and self.__state != "established":
                self.__handshake_complete()
        except Exception, e:
            log.warn("got a certificate request from an invalid source: %s" % e.message)
            return message.Error(errcode.UNAUTHORIZED, "invalid certificate")
        return message.Certificate(self.securityLayer)

    def init_handshake(self):
        """Initializes a handshake with the other side.

        send a certificate request that is signed from us and contains
        our own public key.
        """
        log.info("initializing Message Layer Security...")
        req = message.CertificateRequest()
        msg = self.securityLayer.sign(req.as_xml(), include_certificate=True)[0]
        self.__state == "handshaking"
        self.sendMessage(msg)

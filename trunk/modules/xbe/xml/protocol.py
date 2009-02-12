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
The Xen Based Execution Environment XML Protocol
"""

import logging, threading
log = logging.getLogger(__name__)

from pprint import pformat

from xbe.xml.namespaces import *
from xbe.xml import message, errcode
from xbe.xml.security_exceptions import *

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

    def connectionLost(self):
        pass
    
    def dispatch(self, elem, *args, **kw):
        try:
            method = getattr(self, "do_%s" % (decodeTag(elem.tag)[1]))
        except AttributeError:
            log.warn("no such method: do_%s" % (decodeTag(elem.tag)[1]))
        else:
            try:
                rv = method(elem, *args, **kw)
            except Exception, e:
                from traceback import format_exc
                log.warn("exception during message handling: %s\n%s" % (e, format_exc(e)))
            else:
                return rv

    def addUnderstood(self, tag):
        if tag not in self.__understood:
            self.__understood.append(tag)

    def transformResultToMessage(self, result):
        if result is None:
            # do not reply, so return None
            return None

        if isinstance(result, failure.Failure):
            log.warn("failure occured: %s\n%s" %
                     (result.getErrorMessage(), result.getTraceback()))
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

    def parse_and_validate(self, msg):
        if isinstance(msg, basestring):
            xml = etree.fromstring(msg)
        else:
            xml = msg
        # validate xml against schema
        assert (isinstance(xml, (etree._Element, etree._ElementTree)))
        return xml

    def messageReceived(self, msg):
        """Handle an incoming XML message.

        The message handling code works as follows:

             * a method is looked up according to the 'tag' of the root element
               or the first direct child that 
        """
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
        error = message.MessageBuilder.from_xml(err.getroottree())
        log.error("got error:\n%s" % repr(error))

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
    
    def __init__(self, cert, ca_cert,
                 certificate_checker=None,
                 protocolFactory=None, *protocolFactoryArgs, **protocolFactoryKwArgs):
        XMLProtocol.__init__(self)
        if protocolFactory:
            self.protocolFactory = protocolFactory
            self.protocolFactoryArgs = protocolFactoryArgs
            self.protocolFactoryKwArgs = protocolFactoryKwArgs
        self.__certificate_checker = certificate_checker
        self.__cert = cert
	self.__other_cert = None
        self.__ca_cert = ca_cert
        self.__state = "disconnected"
        self.mtx = threading.RLock()
        self.__message_queue = []

    def do_EstablishMLS(self, elem, *a, **kw):
        """handle a MLS establish request."""
        
        if isinstance(elem, etree._Element):
            root = elem.getroottree().getroot()
        elif isinstance(elem, etree._ElementTree):
            root = elem.getroot()
        other_state = root.find(XBE("MessageBody/EstablishMLS")).attrib["state"]

        from xbe.xml.security import X509SecurityLayer
        if self.__state == "disconnected":
            try:
                # initialize the security layer
                securityLayer = X509SecurityLayer(self.__cert, # my own certificate
                                                  None, # the other's certificate
                                                  [self.__ca_cert])
                
                securityLayer.validate(root)

                # check the certificate with some certificate checker
                # stay in state 'disconnected' if the check fails
                if self.__certificate_checker is not None:
                    other_cert = securityLayer.other_cert()
                    if not self.__certificate_checker(other_cert):
                        raise SecurityError("user not allowed", other_cert)
            except ValidationError, e:
                # could not validate, stay in disconnected
                log.warn("Message Layer Security handshake *failed*: %s" % str(e))
                msg = message.Error(errcode.SECURITY_ERROR, "could not validate message")
            except SecurityError, e:
                log.info("user not permitted")
                msg = message.Error(errcode.UNAUTHORIZED, "you are not authorized")
            except Exception, e:
                log.warn("Message Layer Security handshake *failed*: %s" % str(e))
                msg = message.Error(errcode.SECURITY_ERROR, str(e))
            else:
                # everything is fine
                self.__establish(securityLayer)

                # if the other side is in state 'disconnected', send a
                # EstablishMLS  message and indicate,  that we  are in
                # state established
                if other_state == message.EstablishMLS.ST_DISCONNECTED:
                    my_state = message.EstablishMLS.ST_ESTABLISHED
                    msg = message.EstablishMLS(self.__securityLayer, my_state)
                else:
                    msg = None
            return msg

        if self.__state == "established":
            try:
                self.__securityLayer.validate(root)
            except SecurityError, e:
                msg = message.Error(errcode.SECURITY_ERROR, "could not validate message")
                self.__disconnect()
            else:
                # if the other side is in state 'disconnected', send a
                # EstablishMLS  message and indicate,  that we  are in
                # state established
                if other_state == message.EstablishMLS.ST_DISCONNECTED:
                    my_state = message.EstablishMLS.ST_ESTABLISHED
                    msg = message.EstablishMLS(self.__securityLayer, my_state)
                else:
                    msg = None
            return msg

    def __establish(self, layer):
        log.info("Message Layer Security established")
        self.__securityLayer = layer
	self.__other_cert = layer.other_cert()
        self.__state = "established"

        # instantiate the upper protocol
        if self.protocolFactory:
            log.info("attaching application layer")
            self.protocol = self.protocolFactory(*self.protocolFactoryArgs,
                                                 **self.protocolFactoryKwArgs)
            try:
                factory = self.factory
            except AttributeError:
                pass
            else:
                self.protocol.factory = factory

            # connect it with a secure transport
            # (thus we act as a secure lower layer)
            self.protocol.makeConnection(
                SecureXMLTransport(self.transport, self.__securityLayer))

        # check if messages are pending
        while len(self.__message_queue) > 0:
            msg = self.__message_queue.pop(0)
            try:
                self.messageReceived(msg)
            except Exception, e:
                log.info("could not handle pending message")

    def __disconnect(self):
        log.info("disconnecting...")
        try:
            p = self.protocol
            del self.protocol
        except AttributeError:
            pass
        else:
            p.connectionLost()
            
        try:
            del self.__securityLayer
        except AttributeError:
            pass
        self.__state = "disconnected"

    # handle security related messages
    def do_Message(self, xml):
        try:
            msg_obj = message.MessageBuilder.from_xml(xml)
            if isinstance(msg_obj, message.Error):
                log.debug("got error: %r", msg_obj)
                self.__disconnect()
                raise SecurityError("got error", msg_obj)
        except SecurityError:
            return
        except Exception:
            pass

        # decompose into header and body
        hdr = xml.find(XBE("MessageHeader"))
        bod = xml.find(XBE("MessageBody"))

        if hdr is None:
            log.error("ignoring illegal message: '%r'" % (etree.tostring(xml)))
            return

        # is it a EstablishMLS message
        if bod is not None and bod.find(XBE("EstablishMLS")) is not None:
            return self.do_EstablishMLS(xml)

        #
        # if we are still disconnected but got some encrypted data,
        # remember the message in our queue and establish the MLS first
        #
        if self.__state == "disconnected":
            log.debug("i am still disconnected, remembering message")
            self.__message_queue.append(xml)
            from xbe.xml.security import X509SecurityLayer

            securityLayer = X509SecurityLayer(self.__cert, # my own certificate
                                              None, # the other's certificate
                                              [self.__ca_cert])
            my_state = message.EstablishMLS.ST_DISCONNECTED
            return message.EstablishMLS(securityLayer, my_state)

        # throw away empty messages
        if not bod or not len(bod):
            log.debug("throwing away empty message")
            return None
        
        if self.__state == "established":
            return self.dispatch(bod[0], xml)

    def do_CipherData(self, cipherdata, msg):
        """handle ciphered data.

        decrypts the received data and validates it.
        """
        # decrypt the whole message and validate it
        try:
            real_msg = self.__securityLayer.decrypt(msg)
        except Exception, e:
            from traceback import format_exc
            log.error("decyphering *failed*: %s\n%s" % (e, format_exc(e)))
            self.__disconnect()
            return message.Error(errcode.DECYPHER_FAILED)
        # validate the message
        try:
            real_msg = self.__securityLayer.validate(real_msg)
        except SecurityError, se:
            log.debug("could not validate message: %s: %s", etree.tostring(real_msg), se)
            return message.Error(errcode.SIGNATURE_MISSMATCH)
        try:
            rv = self.protocol.messageReceived(real_msg)
        except Exception, e:
            log.debug("handling of application data failed", exc_info=1)
        else:
            return rv

    def init_handshake(self):
        """Initializes a handshake with the other side."""
        log.info("initializing Message Layer Security...")
        from xbe.xml.security import X509SecurityLayer

        securityLayer = X509SecurityLayer(self.__cert, # my own certificate
                                          None, # the other's certificate
                                          [self.__ca_cert])
        my_state = message.EstablishMLS.ST_DISCONNECTED
        msg = message.EstablishMLS(securityLayer, my_state)
        self.sendMessage(msg)

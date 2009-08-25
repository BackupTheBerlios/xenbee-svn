# XenBEE is a software that provides remote execution of applications
# in self-contained virtual disk images via Xen.
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


"""The common XBE protocol base.

It simply builds on the STOMP protocol and dispatches received
messages to special XML protocol instances.

"""

import logging, re
log = logging.getLogger(__name__)

from xbe.stomp.proto import StompClient, StompClientFactory, StompTransport
from xbe.xml.protocol import XMLTransport
# Twisted imports
from twisted.internet import reactor

class XenBEEStompProtocol(StompClient):
    """Processing input received by the STOMP server."""

    def __init__(self):
	self.factory = None
	StompClient.__init__(self)

    def connectedReceived(self, _):
	# i am connected to the stomp server
	log.debug("successfully connected to STOMP server, avaiting your commands.")
        self.setReplyTo(self.factory.queue)
	self.subscribe(self.factory.queue, auto_ack=True, exclusive=True)
        self.post_connect()
    

class XenBEEProtocol(StompClient):
    """Processing input received by the STOMP server."""

    def __init__(self):
	log.debug("initializing XenBEE protocol...")
	self.factory = None
	StompClient.__init__(self)

    def connectedReceived(self, _):
	# i am connected to the stomp server
	log.debug("successfully connected to STOMP server, avaiting your commands.")
        self.setReplyTo(self.factory.queue)

        log.debug("TODO: move the subscription code to the client protocol")
	self.subscribe(self.factory.queue, auto_ack=True, exclusive=True)

        self.factory.stompConnectionMade(self)

    def _messageReceived(self, msg):
        # use the reply-to field
        try:
            replyTo = msg.header["reply-to"]
        except (KeyError, ValueError):
	    log.warn("message without reply-to received, throwing away")
            return
        else:
            if replyTo == "null":
                log.warn("got message with 'null' reply-to, throwing away")
                return

        # dispatch the message to another protocol using the MOM identifier
        pattern = r'^/(queue|topic)/'
        momIdentifier = re.sub(pattern, "", replyTo)
        components = momIdentifier.split(".", 2)
        try:
            transport = XMLTransport(StompTransport(self, replyTo))
            self.factory.dispatchToProtocol(transport, msg.body, *components)
        except Exception, e:
            log.error("could not dispatch according to MOM identifier: %s", momIdentifier, exc_info=1)
            
    def messageReceived(self, msg):
        reactor.callInThread(self._messageReceived, msg)

    def errorOccured(self, msg, detail):
	log.error("error-message: '%s', details: '%s'", msg, detail)

class XenBEEProtocolFactory(StompClientFactory):
    """Basic protocol factory.

    Override the dispatchToProtocol method to handle XML messages in special protocols.

    """
    protocol = XenBEEProtocol

    def __init__(self, queue, user, password="none"):
	log.debug("initializing XenBEE protocol factory...")
	StompClientFactory.__init__(self, user=user, password=password)
	self.queue = queue

    def dispatchToProtocol(self, transport, msg, domain, sourceType, sourceId=None):
        """Called when a message is received.

        @param transport - the transport over which the client is reachable
        @param msg - the message that we received
        @param domain - the first part of the MOM-identifier
               (e.g. xenbee.daemon -> domain is 'xenbee')
        @param sourceType - the type of client that sent the message
               (e.g. xenbee.client.foo -> type is 'client')
        @param sourceId - the source identifier
               (e.g. xenbee.client.12345 -> id is 12345)
        """
        raise NotImplementedError("dispatchToProtocol must be overridded in subclass")

    def clientConnectionFailed(self, connector, reason):
	log.error("connection to STOMP server failed!: %s" % (str(reason.value)))
	if 'twisted.internet.error.ConnectionRefusedError' in reason.parents:
            log.info("shutting down...")
            reactor.exitcode = 1
            reactor.stop()
	else:
	    StompClientFactory.clientConnectionFailed(self, connector, reason)

    def stompConnectionMade(self, stomp_protocol):
        """called when we are connected to the STOMP server"""
        pass


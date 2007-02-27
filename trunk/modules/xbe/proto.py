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
	self.factory = None
	StompClient.__init__(self)

    def connectedReceived(self, _):
	# i am connected to the stomp server
	log.debug("successfully connected to STOMP server, avaiting your commands.")
        self.factory.stompConnectionMade(self)

        log.error("TODO: move the subscription code to the client protocol")
        self.setReplyTo(self.factory.queue)
	self.subscribe(self.factory.queue, auto_ack=True, exclusive=True)

    def _messageReceived(self, msg):
        # check if we got an advisory from the activemq server
#        log.debug("got message:\n%s" % (str(msg),))

        # use the reply-to field
        try:
            replyTo = msg.header["reply-to"]
            if replyTo == "null":
                raise ValueError
        except (KeyError, ValueError):
	    log.warn("message without reply-to received, throwing away")
            return

        # dispatch the message to another protocol using the MOM identifier
        pattern = r'^/(queue|topic)/'
        momIdentifier = re.sub(pattern, "", replyTo)
        components = momIdentifier.split(".", 2)
        try:
            log.debug("dispatching: " + momIdentifier)
            transport = XMLTransport(StompTransport(self, replyTo))
            log.debug("transport type: %r" % transport)
            self.factory.dispatchToProtocol(transport, msg.body, *components)
        except Exception, e:
            log.error(
                "could not dispatch according to MOM identifier: %s: %s" % (
                momIdentifier, e))
            
    def messageReceived(self, msg):
        reactor.callInThread(self._messageReceived, msg)

    def errorOccured(self, msg, detail):
	log.error("error-message: '%s', details: '%s'" % (msg, detail))

class XenBEEProtocolFactory(StompClientFactory):
    """Basic protocol factory.

    Override the dispatchToProtocol method to handle XML messages in special protocols.

    """
    protocol = XenBEEProtocol

    def __init__(self, queue, user, password="none"):
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

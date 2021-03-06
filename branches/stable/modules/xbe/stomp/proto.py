"""Implementation of the STOMP protocol (client side).

see: http://stomp.codehaus.org/Protocol

"""

import re, threading, time, os, logging
log = logging.getLogger(__name__)

# twisted imports
from twisted.protocols.basic import LineReceiver
from twisted.internet import defer, reactor, threads, protocol, interfaces
from twisted.internet.protocol import ReconnectingClientFactory
from textwrap import dedent

from xbe.util.uuid import uuid

import errno

__all__ = [ 'StompClient', 'Message', 'StompClientFactory' ]

class reason:
    def __init__(self, errcode, msg=None):
        self.errcode = errcode
        self.msg = msg or os.strerror(errcode)

class Frame:
    """This class represents a 'frame'.

    A frame consists of a 'type' field which describes its
    meaning, a header which holds (key,value) pairs (such as
    'content-length') and some data belonging to this frame.

    Example Frame:

	MESSAGE
	content-length: 5

	hello!\x00\x0a

    """
    def __init__(self, frame_type):
	self.type = frame_type
	self.header = {}
	self.data = ""

    def remainingBytes(self):
	"""Return the number of bytes that are still needed to complete this frame.

	returns 0 if no more bytes are needed or the frame does not have a content-length header.
	returns > 0 if bytes are remaining and a content-length was specified.

	"""
	if self.hasContentLength():
	    return self.contentLength() - len(self.data)
	else:
	    return 0

    def hasContentLength(self):
	"""return True iff a content-length has been given."""
	return self.header.has_key("content-length")

    def contentLength(self):
	"""return the content-length if one was given, raises KeyError otherwise."""
	return int(self.header.get("content-length"))

    def __str__(self):
	s = [ "%s\n" % self.type ]
	for k,v in self.header.iteritems():
	    s.append( "%s: %s\n" % (k,v) )
	s.append("\n")
	if len(self.data):
	    s.append(self.data)
	s.append('\x00\x0a')
	return "".join(s)

class Message:
    """Holds a single message, containing header and body."""
    def __init__(self, header, body, queue):
	self.header = header
	self.body = body
	self.queue = queue

    def __str__(self):
        s = []
	for k,v in self.header.iteritems():
	    s.append( "%s: %s\n" % (k,v) )
	s.append("\n")
	if len(self.body):
	    s.append(self.body)
	s.append('\x00\x0a')
	return "".join(s)

class StompTransport:
    """Simply wraps the message sending to write(text).

    Uses an existing STOMP Connection and a destination queue to send
    its data.
    """
    
    def __init__(self, stompConn, queue, ttl=15*60*1000):
	"""Initialize the transport.

        @param stompConn, the stomp protocol to be used
        @param queue the destination queue
        @param ttl the default TTL for sent messages (defaults to 15min)
        """
	self.stomp = stompConn
	self.queue = queue
        self.ttl = ttl

    def write(self, data, *args, **kw):
	"""Write data to the destination queue."""
        return threads.deferToThread(self.stomp.send,
                                     self.queue,
                                     str(data), self.ttl, *args, **kw)
        
class StompClient(LineReceiver):
    """Implementation of the STOMP protocol - client side.

    Uses the twisted LineReceiver to implement the protocol
    details.

    """

    auto_connect = True
    timeout = 10 # timeout of ten seconds for an answer

    def __init__(self, username='', password=''):
	"""Initializes the client."""
	self.frame = None
	self.state = "disconnected"
	self.transaction = None
	self.session = None
        self.replyTo = None
	self.mode = "command"
	self.delimiter = '\n'
	self.terminator = "\x00\x0a"
	self.buffer = ''
	self.defer = None
        self.factory = None
        self.mtx = threading.RLock()
        self.timeoutTimer = None

        self.user = username
        self.password = password

    def setReplyTo(self, replyTo):
        self.replyTo = replyTo

    def makeConnection(self, transport):
        self.transport = transport
        
	if self.auto_connect and self.state == "disconnected":
            def _s(arg):
                self.connected = 1
                self.connectionMade()
            def _f(arg):
                pass
	    self.connect(self.factory.user,
                         self.factory.password).addCallback(_s).addErrback(_f)
        

    def connectionMade(self):
	"""Called when connection has been established."""
        pass
#	if self.auto_connect and self.state == "disconnected":
#            def _s(arg):
#                pass
#            def _f(arg):
#                pass
#	    self.connect(self.factory.user,
#                         self.factory.password).addCallback(_s).addErrback(_f)

    def sendFrame(self, frame):
	"""Send a frame."""
        try:
            self.mtx.acquire()
#            log.debug(frame)
            self.transport.write(str(frame))
        finally:
            self.mtx.release()

    def lineReceived(self, line):
	"""Handle a new line."""
	line = line.strip()
	if self.mode == "command":
	    # ignore any empty lines before a new command
	    if not len(line):
		return

	    cmd = line.upper()
	    if re.search('\s+', cmd):
		self.disconnect()
		return

	    # got new command
	    self.frame = Frame(line.upper())
	    self.mode = "header"
	    return

	# parse header
	elif self.mode == "header":
	    # end of header reached?
	    if not len(line):
		self.mode = "data"
		self.setRawMode()
		return

	    # read header
	    try:
		k,v = [ p.strip() for p in line.split(':', 1) ]
		self.frame.header[k] = v
	    except ValueError:
		# could not get header element, this is an error condition
		self.disconnect()
		return

    def closeFrame(self, remaining=''):
	"""finish the current frame."""
	f, self.frame = self.frame, None

	# call back
	self.handleFrame(f)

	self.mode = "command"
	self.setLineMode(remaining)

    def rawDataReceived(self, data):
	"""reads raw data received from the socket.

	Used to read the data part of a frame, since it may
	not be line-oriented.

	I.  no content-length:
	    * read until 'terminator' character code is reached (default: \x00\x0a)
	    * close frame
	    * handle remaining data line oriented

	II. content-length available:
	    * read data into frame until content-length bytes have been read.
	    * handle rest as line oriented

	"""
	f = self.frame

	# if frame does not  have a content length, read until
	# the termination code arrives.
	if not f.hasContentLength():
	    try:
		idx = data.index(self.terminator)
		f.data += data[0:idx]
		self.closeFrame(data[idx+1:])
	    except ValueError:
		f.data += data
	    return

	# if  frame contains content-length,  read as  many as
	# content-length bytes
	max_new_bytes = min(len(data), f.remainingBytes())
	tmp = data[0:max_new_bytes]
	f.data += tmp
	data = data[max_new_bytes+1:]

	if f.remainingBytes() == 0:
	    self.closeFrame(data)

    def has_expired(self, frame):
        expires = long(frame.header.get("expires", 0))
        now = long(time.time()*1000)
        if expires is not None and expires > 0:
            return now > expires
        return False
    
    def handleFrame(self, frame):
	if frame.type == "CONNECTED":
	    self.handle_CONNECTED(frame)
	elif frame.type == "MESSAGE":
            if self.has_expired(frame):
                log.debug("throwing away expired frame")
                return
	    msg = Message(frame.header, frame.data, frame.header["destination"])
            if self.defer:
                if self.timeoutTimer:
                    self.timeoutTimer.cancel()
                    self.timeoutTimer = None
                self.defer.callback(msg)
                self.defer = None
	    self.messageReceived(msg)
	elif frame.type == "ERROR":
            msg = frame.header["message"]
	    self.errorOccurred(msg, frame.data)
            if self.defer:
                self.defer.errback(msg)
                self.defer = None

    def handle_CONNECTED(self, frame):
	self.state = "connected"
        if self.timeoutTimer:
            self.timeoutTimer.cancel()
            del self.timeoutTimer
	self.connectedReceived(frame)
	if self.connectDefer:
	    self.connectDefer.callback(frame)
	    del self.connectDefer

    def connect(self, user, password, time_out=timeout):
	"""Connect to the STOMP server, using 'user' and 'password'."""
	f = Frame("CONNECT")
	f.header["login"] = user
	f.header["passcode"] = password
	self.sendFrame(f)

        r = reason(errno.ETIMEDOUT)
        def _f(_reason):
            self.connectFailed(_reason)
            self.connectDefer.errback(_reason)
            self.connectDefer = None

        self.timeoutTimer = reactor.callLater(time_out, _f, r)
	self.connectDefer = defer.Deferred()
	return self.connectDefer

    def receive(self, time_out=None):
	"""Await the reception of a message.

	Returns a 'deferred' object.

	"""
        if time_out:
            def _t(_reason):
                self.defer.errback(_reason)
                self.defer = None
            r = reason(errno.ETIMEDOUT)
            self.timeoutTimer = reactor.callLater(time_out, _t, r)
            
	self.defer = defer.Deferred()
	return self.defer

    def connectedReceived(self, frame):
	"""Called when we are logged in to the STOMP server.

	Override this method.

	"""
	pass

    def connectFailed(self, reason):
        """Called when we could not connect to the stomp server.

        Reason is an object with the following properties:
           msg - a small description of the reason
           errcode - the error code (see the errno module)

        Override this method.
        """
        pass

    # callbacks
    def messageReceived(self, msg):
	"""A message has been received.

	msg -- a Message object, containing all header fields and the body.
	queue -- the queue in which the message has been received.

	Override this method.
	"""

    def errorOccurred(self, msg, detail):
	"""Called when the server found an error.

	Override this method.

	"""

    # client protocol

    def send(self, queue, msg, ttl=0, **kw):
	"""Send a message to a specific queue.

	header -- a dictionary of header fields
	msg -- the body of the message to be sent
        ttl -- the time to live for this message in milliseconds
	queue -- the destination queue

	"""
        try:
            self.mtx.acquire()
            if not queue or not len(queue):
                raise RuntimeError("destination queue must not be empty: '%s'" % str(queue))
            f = Frame("SEND")
            f.header.update(kw)
            f.header["destination"] = queue
            if self.replyTo:
                f.header["reply-to"] = self.replyTo
            f.data = msg
            if self.transaction:
                f.header["transaction"] = self.transaction
            f.header["content-length"] = len(msg)
            if ttl:
                f.header["expires"] = long((time.time() * 1000) + ttl)
            else:
                f.header["expires"] = 0
        finally:
            self.mtx.release()
        self.sendFrame(f)

    def subscribe(self, queue, exclusive=False, auto_ack=True):
	"""Subscribe to queue 'queue'.

	When subscribed to a queue, the client receives all
	messages targeted at that queue.

        exclusive -- ActiveMQ extension: boolean: Would I like to be an Exclusive Consumer on a queue
	auto_ack -- if True, all messages are automatically acknowledged,
	    otherwise a seperate 'ack' has to be sent.

	"""
	f = Frame("SUBSCRIBE")
	f.header["destination"] = queue
        f.header["activemq.exclusive"] = exclusive
        if auto_ack:
            f.header["ack"] = "auto"
        else:
            f.header["ack"] = "client"
	self.sendFrame(f)

    def unsubscribe(self, queue):
	"""Remove the subscription to some queue."""
	f = Frame("UNSUBSCRIBE")
	f.header["destination"] = queue
	self.sendFrame(f)

    def ack(self, msgid):
	"""Acknowledge the given message id."""
	f = Frame("ACK")
	f.header["message-id"] = msgid
	if self.transaction:
	    f.header["transaction"] = self.transaction
	self.sendFrame(f)

    def begin(self):
	"""Begin a new transaction."""
	if self.transaction:
	    raise RuntimeError("currently only one active transaction is supported!")
	self.transaction = uuid()
	f = Frame("BEGIN")
	f.header["transaction"] = self.transaction
	self.sendFrame(f)

    def abort(self):
	"""Abort an ongoing transaction."""
	if not self.transaction:
	    raise RuntimeError("no currently active transaction")
	f = Frame("ABORT")
	f.header["transaction"] = self.transaction
	self.transaction = None
	self.sendFrame(f)

    def commit(self):
	"""Commit the current transaction."""
	if not self.transaction:
	    raise RuntimeError("no currently active transaction")
	f = Frame("COMMIT")
	f.header["transaction"] = self.transaction
	self.transaction = None
	self.sendFrame(f)

    def disconnect(self):
	"""Disconnect from the server."""
	if self.state == "connected":
	    f = Frame("DISCONNECT")
	    self.sendFrame(f)
	    self.transport.loseConnection()
	    self.session = None
	self.state = "disconnected"

    def __del__(self):
	self.disconnect()

class StompClientFactory(ReconnectingClientFactory):
    protocol = StompClient
    maxRetries = 5

    def __init__(self, user = '', password = ''):
	self.user = user
	self.password = password

    def clientConnectionFailed(self, connector, reason):
        if self.retries > self.maxRetries:
            log.warn("connecting failed, giving up")
            reactor.exitcode = 2
            reactor.stop()
        else:
            log.info("connection failed, retrying...")
            self.retry(connector)

class ProtocolTransportMixin:
    """This class has been taken from twisted.conch.telnet."""
    def write(self, bytes):
        self.transport.write(bytes)

    def writeSequence(self, seq):
        self.transport.writeSequence(seq)

    def loseConnection(self):
        self.transport.loseConnection()

    def getHost(self):
        return self.transport.getHost()

    def getPeer(self):
        return self.transport.getPeer()

class StompTransport2(StompClient, ProtocolTransportMixin):
    disconnecting = False

    protocolFactory = None
    protocol = None

    def __init__(self, protocolFactory=None, *a, **kw):
        StompClient.__init__(self)
        if protocolFactory is not None:
            self.protocolFactory = protocolFactory
            self.protocolFactoryArgs = a
            self.protocolFactoryKwArgs = kw

    def connectionMade(self):
        self.subscribe(self.queue)
        if self.protocolFactory is not None:
            self.protocol = self.protocolFactory(*self.protocolFactoryArgs, **self.protocolFactoryKwArgs)
            log.debug("connected protocol: %r" % (self.protocol))
            try:
                factory = self.factory
            except AttributeError:
                pass
            else:
                self.protocol.factory = factory
            self.protocol.makeConnection(self)

    def connectionLost(self, reason):
        StompClient.connectionLost(self, reason)
        if self.protocol is not None:
            try:
                self.protocol.connectionLost(reason)
            finally:
                del self.protocol
        
    def write(self, bytes):
        ProtocolTransportMixin.write(self, bytes)

def selftest(host="localhost", port=61613):
    class StompClientTest(StompClient):
	def __init__(self):
	    StompClient.__init__(self)
	    self.client_id = uuid()

	def send(self, msg):
	    StompClient.send(self, queue="/queue/stomptest.test-daemon",
			     msg=msg, **{"client-id": self.client_id})

	def connectedReceived(self, frame):
	    self.subscribe("/queue/stomptest.client.%s"%self.client_id, auto_ack=True)
	    self.subscribe("/queue/stomptest.test-daemon", auto_ack=True)
	    msg = """\
	    hello daemon!
	    """
	    self.send(dedent(msg).strip())

	def messageReceived(self, msg):
	    print "got message in queue:", msg.queue
	    print "'%s'" % msg.body

	    if queue == "/queue/stomptest.test-daemon":
		msg = "daemon says hello to %s" % msg.header["client-id"]
		StompClient.send(self, queue="/queue/stomptest.client.%s" % self.client_id,
				 msg=msg)

    f = StompClientFactory()
    f.protocol = StompClientTest
    reactor.connectTCP(host, port, f)
    reactor.run()

if __name__ == '__main__':
    selftest()

"""Implementation of the STOMP protocol (client side).

see: http://stomp.codehaus.org/Protocol

"""

import sys, re

# twisted imports
from twisted.protocols.basic import LineReceiver
from twisted.internet import defer, reactor
from twisted.internet.protocol import ReconnectingClientFactory
from textwrap import dedent
from xenbeed.uuid import uuid

__all__ = [ 'StompClient', 'Message', 'StompClientFactory' ]

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
	return str(self.body)

class StompClient(LineReceiver):
    """Implementation of the STOMP protocol - client side.

    Uses the twisted LineReceiver to implement the protocol
    details.

    """

    auto_connect = True

    def __init__(self):
	"""Initializes the client."""
	self.frame = None
	self.state = "disconnected"
	self.transaction = None
	self.session = None
	self.mode = "command"
	self.delimiter = '\n'
	self.terminator = "\x00\x0a"
	self.buffer = ''
	self.defer = None

    def connectionMade(self):
	"""Called when connection has been established."""
	if self.auto_connect and self.state == "disconnected":
	    self.connect(self.factory.user, self.factory.password)

    def sendFrame(self, frame):
	"""Send a frame."""
	self.transport.write(str(frame))

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
		self.data += data
	    return

	# if  frame contains content-length,  read as  many as
	# content-length bytes
	max_new_bytes = min(len(data), f.remainingBytes())
	tmp = data[0:max_new_bytes]
	f.data += tmp
	data = data[max_new_bytes+1:]

	if f.remainingBytes() == 0:
	    self.closeFrame(data)

    def handleFrame(self, frame):
	if frame.type == "CONNECTED":
	    self.handle_CONNECTED(frame)
	elif frame.type == "MESSAGE":
	    msg = Message(frame.header, frame.data, frame.header["destination"])
	    self.messageReceived(msg)
	elif frame.type == "ERROR":
	    self.errorOccurred(frame.header["message"], frame.data)

    def handle_CONNECTED(self, frame):
	self.state = "connected"
	self.connectedReceived(frame)
	if self.connectDefer:
	    self.connectDefer.callback(frame)
	    self.connectDefer = None

    def connect(self, user, password):
	"""Connect to the STOMP server, using 'user' and 'password'."""
	f = Frame("CONNECT")
	f.header["login"] = user
	f.header["passcode"] = password
	self.sendFrame(f)
	self.connectDefer = defer.Deferred()
	return self.connectDefer

    def receive(self):
	"""Await the reception of a message.

	Returns a 'deferred' object.

	"""
	self.defer = defer.Deferred()
	return self.defer

    def connectedReceived(self, frame):
	"""Called when we are logged in to the STOMP server.

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
	if self.defer:
	    self.defer.callback(msg)
	    self.defer = None

    def errorOccurred(self, msg, detail):
	"""Called when the server found an error.

	Override this method.

	"""
	if self.defer:
	    self.defer.errback(msg)
	    self.defer = None


    # client protocol

    def send(self, queue, msg = '', header={}):
	"""Send a message to a specific queue.

	header -- a dictionary of header fields
	msg -- the body of the message to be sent
	queue -- the destination queue

	"""

	if not queue or not len(queue):
	    raise RuntimeError("destination queue must not be empty: '%s'" % str(queue))
	f = Frame("SEND")
	f.header.update(header)
	f.header["destination"] = queue
	f.data = msg
	if self.transaction:
	    f.header["transaction"] = self.transaction
	f.header["content-length"] = len(msg)
	self.sendFrame(f)

    def subscribe(self, queue, auto_ack=True):
	"""Subscribe to queue 'queue'.

	When subscribed to a queue, the client receives all
	messages targeted at that queue.

	auto_ack -- if True, all messages are automatically acknowledged,
	    otherwise a seperate 'ack' has to be sent.

	"""
	f = Frame("SUBSCRIBE")
	f.header["destination"] = queue
	if auto_ack: f.header["ack"] = "auto"
	else: f.header["ack"] = "client"
	self.sendFrame(f)

    def unsubscribe(self, queue):
	"""Remove the subscription to some queue."""
	f = Frame("SUBSCRIBE")
	f.header["destination"] = queue
	self.sendFrame(f)

    def ack(self, msgid):
	"""Acknowledge the given message id."""
	f = Frame("ACK")
	f.header["message-id"] = msgid
	if self.transaction:
	    frame.header["transaction"] = self.transaction
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

    def __init__(self, user = '', password = ''):
	self.user = user
	self.password = password

    def clientConnectionFailed(self, connector, reason):
	reactor.stop()

def selftest(host="localhost", port=61613):
    class StompClientTest(StompClient):
	def __init__(self):
	    StompClient.__init__(self)
	    self.client_id = uuid()

	def send(self, msg):
	    StompClient.send(self, queue="/queue/xenbee/test-daemon",
			     msg=msg, header={"client-id": self.client_id})

	def connectedReceived(self, frame):
	    self.subscribe("/queue/xenbee/clients/%s"%self.client_id, auto_ack=True)
	    self.subscribe("/queue/xenbee/test-daemon", auto_ack=True)
	    msg = """\
	    hello daemon!
	    """
	    self.send(dedent(msg).strip())

	def messageReceived(self, msg):
	    print "got message in queue:", msg.queue
	    print "'%s'" % msg.body

	    if queue == "/queue/xenbee/test-daemon":
		msg = "daemon says hello to %s" % msg.header["client-id"]
		StompClient.send(self, queue="/queue/xenbee/clients/%s" % self.client_id,
				 msg=msg)

    f = StompClientFactory()
    reactor.connectTCP(host, port, f)
    reactor.run()

if __name__ == '__main__':
    selftest()

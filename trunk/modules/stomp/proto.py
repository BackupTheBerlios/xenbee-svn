"""Implementation of the STOMP protocol (client side)"""

import sys

# twisted imports
from twisted.protocols.basic import LineReceiver
from textwrap import dedent
from xenbeed.uuid import uuid

class Frame:
	def __init__(self, frame_type):
		self.type = frame_type
		self.header = {}
		self.data = ""

	def remainingBytes(self):
		if self.hasContentLength():
			return self.contentLength() - len(self.data)
		else:
			return 1

	def hasContentLength(self):
		return self.header.has_key("content-length")

	def contentLength(self):
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
	def __init__(self, header, body):
		self.header = header
		self.body = body

class StompClient(LineReceiver):
	def __init__(self):
		self.frame = None
		self.transaction = None
		self.session = None
		self.mode = "command"
		self.delimiter = '\n'
		self.terminator = "\x00\x0a"
		self.buffer = ''

	def connectionMade(self):
		f = Frame("CONNECT")
		f.header["login"] = self.factory.user
		f.header["passcode"] = self.factory.password
		self.sendFrame(f)

	def sendFrame(self, frame):
		old_delim, self.delimiter = self.delimiter, ''
		#print >>sys.stderr, "sending frame:\n", frame
		self.sendLine(str(frame))
		self.delimiter = old_delim

	def lineReceived(self, line):
		#print "got line:", line
		if self.mode == "command":
			# ignore any empty lines
			line = line.strip()
			if not len(line):
				return

			# got new command
			cmd = line.upper()
			self.frame = Frame(line.upper())
			self.mode = "header"
			#print >>sys.stderr, "got command:", cmd
			return

		# parse header
		elif self.mode == "header":
			line = line.strip()
			if not len(line):
				#print "switching to raw"
				self.mode = "data"
				self.setRawMode()
				return

			try:
				k,v = [ p.strip() for p in line.split(':', 1) ]
				self.frame.header[k] = v
				#print >>sys.stderr, "got header part:",k,":",v
			except ValueError:
				# could not get header element, so it must be an empty line
				#print >>sys.stderr, "could not parse header field:", line
				self.looseConnection()
				return

	def closeFrame(self, remaining=''):
		f, self.frame = self.frame, None

		# call back
		self.handleFrame(f)

		self.mode = "command"
		self.setLineMode(remaining)

	def rawDataReceived(self, data):
		f = self.frame

		# if frame does not  have a content length, read until
		# the termination code arrives.
		if not f.hasContentLength():
			#print "no content-length"
			if self.terminator in data:
				idx = data.index(self.terminator)
				f.data += data[0:idx]
				self.closeFrame(data[idx+1:])
			else:
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
		#print "got frame:",frame
		if frame.type == "CONNECTED":
			self.handle_CONNECTED(frame)
		elif frame.type == "MESSAGE":
			msg = Message(frame.header, frame.data)
			self.messageReceived(msg, frame.header["destination"])
		elif frame.type == "ERROR":
			self.errorReceived(frame.header["message"], frame.data)

	def handle_CONNECTED(self, frame):
		self.session = frame.header["session"]
		self.connectedReceived()

	def connectedReceived(self):
		pass
		
	# callbacks
	def messageReceived(self, msg, queue):
		raise NotImplementedError("'messageReceived' not implemented")

	def errorReceived(self, msg, detail):
		pass
		
	# client protocol

	def send(self, queue, msg = '', header={}):
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

	def subscribe(self, queue, ack="auto"):
		ack = ack.lower()
		if not ack in ("auto", "client"):
			raise RuntimeError("acknowledge mode must be one of 'auto' or 'client': %s" % ack)
		f = Frame("SUBSCRIBE")
		f.header["destination"] = queue
		f.header["ack"] = ack
		self.sendFrame(f)

	def unsubscribe(self, queue):
		f = Frame("SUBSCRIBE")
		f.header["destination"] = queue
		self.sendFrame(f)

	def ack(self, msgid):
		f = Frame("ACK")
		f.header["message-id"] = msgid
		if self.transaction:
			frame.header["transaction"] = self.transaction
		self.sendFrame(f)

	def begin(self):
		if self.transaction:
			raise RuntimeError("currently only one active transaction is supported!")
		self.transaction = uuid()
		f = Frame("BEGIN")
		f.header["transaction"] = self.transaction
		self.sendFrame(f)

	def abort(self):
		if not self.transaction:
			raise RuntimeError("no currently active transaction")
		f = Frame("ABORT")
		f.header["transaction"] = self.transaction
		self.transaction = None
		self.sendFrame(f)

	def commit(self):
		if not self.transaction:
			raise RuntimeError("no currently active transaction")
		f = Frame("COMMIT")
		f.header["transaction"] = self.transaction
		self.transaction = None
		self.sendFrame(f)

	def disconnect(self):
		f = Frame("DISCONNECT")
		self.sendFrame(f)
		self.looseConnection()
		self.session = None

def selftest(host="localhost", port=61613):
	from twisted.internet.protocol import ClientFactory
	from twisted.internet import reactor

	class StompClientTest(StompClient):
		def __init__(self):
			StompClient.__init__(self)
			self.client_id = uuid()

		def send(self, msg):
			StompClient.send(self, queue="/queue/xenbee/daemon",
					 msg=msg, header={"client-id": self.client_id})

		def connectedReceived(self):

			self.subscribe("/queue/xenbee/clients/%s"%self.client_id, ack="auto")
			self.subscribe("/queue/xenbee/daemon", ack="auto")
			msg = """\
			hello daemon!
			"""
			self.send(dedent(msg).strip())

		def messageReceived(self, msg, queue):
			print "got message in queue:", queue
			print "'%s'" % msg.body

			if queue == "/queue/xenbee/daemon":
				msg = "daemon says hello to %s" % msg.header["client-id"]
				StompClient.send(self, queue="/queue/xenbee/clients/%s" % self.client_id,
						 msg=msg)

	f = ClientFactory()
	f.protocol = StompClientTest
	f.user = ""
	f.password = ""

	reactor.connectTCP(host, port, f)
	reactor.run()

if __name__ == '__main__':
	selftest()

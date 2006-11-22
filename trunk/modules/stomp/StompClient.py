"""Implementation of the STOMP protocol (client side)"""

# twisted imports
from twisted.protocols.basic import LineReceiver
import sys

class StompClient(LineReceiver):
	delimiter = '\n'

	def __init__(self):
		self.__moreData = False

	def connectionMade(self):
		sys.stderr.write("connection made\n")
		self.sendLine("CONNECT")
		self.sendLine("login: %s" % self.factory.user)
		self.sendLine("passcode: %s" % self.factory.password)
		self.sendLine("")
		self.sendLine("\x00\x0a")

	def lineReceived(self, line):
		sys.stderr.write("got line: %s\n" % line)	
		if line == "CONNECTED":
			self.__moreData = True

	# callbacks

def selftest(host="localhost", port=61613):
	from twisted.internet.protocol import ClientFactory
	from twisted.internet import reactor

	f = ClientFactory()
	f.protocol = StompClient
	f.user = ""
	f.password = ""

	reactor.connectTCP(host, port, f)
	reactor.run()

if __name__ == '__main__':
	selftest()


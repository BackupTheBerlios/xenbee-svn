#!/usr/bin/env python
"""Example to use the UNIX socket server"""

LOGFILE = '/tmp/xenbeed.log'

# Setup log file
from twisted.python import log
log.startLogging(open(LOGFILE, 'a'))
import sys
sys.stderr = log.logfile

# Twisted imports
from twisted.internet import reactor, stdio
from twisted.internet.protocol import Protocol, Factory
from twisted.protocols import basic

import os, os.path
from syslog import syslog, openlog, LOG_MAIL

class TestProtocol(basic.LineReceiver):
	"""Processing input on a UNIX socket.
	"""

	def connectionMade(self):
		log.msg('Connection from %r' % self.transport)
		self.sendLine('Hello!')

	def lineReceived(self, line):
		log.msg('got line: %s' % line)
		self.sendLine("you wrote: %s" % line)

def main():
	# listen on the unix socket
	f = Factory()
	f.protocol = TestProtocol
	reactor.listenUNIX("/var/lib/xenbeed/xenbeed-socket", f, 10)
	reactor.run()

if __name__ == "__main__":
	main()


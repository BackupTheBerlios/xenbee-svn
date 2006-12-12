#!/usr/bin/env python
"""
The Xen Based Execution Environment protocol
"""

__version__ = "$Rev$"
__author__ = "$Author$"


# Twisted imports
from twisted.python import log
from twisted.internet import reactor, stdio
from twisted.internet.protocol import Protocol, Factory
from twisted.protocols import basic

import os, os.path
from syslog import syslog, openlog, LOG_MAIL

class XenBEEProtocol(basic.LineReceiver):
	"""Processing input on one of the sockets
	"""

	cnt = 0

	def __init__(self):
		XenBEEProtocol.cnt = XenBEEProtocol.cnt + 1
		self.counter = XenBEEProtocol.cnt

	def connectionMade(self):
		log.msg('Connection from %r' % self.transport)
		self.sendLine('XenBEE server')

	def lineReceived(self, line):
		log.msg('got line: %s' % line)
		self.sendLine("you wrote: %s" % line)


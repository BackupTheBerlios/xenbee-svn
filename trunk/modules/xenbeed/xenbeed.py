#!/usr/bin/env python
"""
The Xen Based Execution Environment managing daemon
"""

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

from proto import XenBEEProtocol

def main():
	# listen on the unix socket
	f = Factory()
	f.protocol = XenBEEProtocol
	reactor.listenUNIX("/var/lib/xenbeed/xenbeed-socket", f, 10)
	reactor.listenTCP(1234, f)
	reactor.run()

if __name__ == "__main__":
	main()


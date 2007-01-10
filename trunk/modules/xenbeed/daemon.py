"""
The XenBee daemon.
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging
log = logging.getLogger(__name__)

import sys

# Twisted imports
from twisted.internet import reactor
from xenbeed.proto import XenBEEProtocol, XenBEEProtocolFactory
from urlparse import urlparse

class Daemon:
    def __init__(self, argv=sys.argv):
	"""Initializes the Daemon."""
        self.argv = argv
        self.server = ('localhost', 61613)
        
    def run(self, daemonize=False):
	""""""
	log.debug("starting the XenBEE daemon")
        from twisted.python import threadable
        threadable.init()
        
        # connect to stomp server
        reactor.connectTCP(self.server[0],
                           self.server[1],
                           XenBEEProtocolFactory(queue="/queue/xenbee/daemon"))
        reactor.run()
        return 0

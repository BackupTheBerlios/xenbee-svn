"""
The XenBee daemon.
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging
log = logging.getLogger(__name__)

import sys

import xenbeed
xenbeed.initLogging()

# Twisted imports
from twisted.internet import reactor
from xenbeed.proto import XenBEEProtocol, XenBEEProtocolFactory
from xenbeed.scheduler import Scheduler
from xenbeed.instance import InstanceManager
from xenbeed.task import TaskManager
from urlparse import urlparse

class Daemon:
    def __init__(self, argv=sys.argv):
	"""Initializes the Daemon."""
        self.argv = argv
        self.server = ('localhost', 61613)
        self.instanceManager = InstanceManager('/srv/xen-images/xenbee')
        self.taskManager = TaskManager('/srv/xen-images/xenbee')
        self.scheduler = Scheduler(self.instanceManager, self.taskManager)
        
    def run(self, daemonize=False):
	""""""
	log.debug("starting the XenBEE daemon")
        from twisted.python import threadable
        threadable.init()
        
        # connect to stomp server
        reactor.connectTCP(self.server[0],
                           self.server[1],
                           XenBEEProtocolFactory(self.scheduler,
                                                 queue="/queue/xenbee.daemon"))
        reactor.run()
        return 0

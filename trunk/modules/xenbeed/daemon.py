"""
The XenBee daemon.
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import xenbeed

import logging
log = logging.getLogger(__name__)

import sys

# Twisted imports
from twisted.python import threadable
threadable.init()
from twisted.internet import reactor

from xenbeed.proto import XenBEEProtocol, XenBEEProtocolFactory
from urlparse import urlparse
from optparse import OptionParser

class Daemon:
    def __init__(self, argv=sys.argv):
	"""Initializes the Daemon."""
        self.argv = argv
        p = OptionParser()
        p.add_option("-H", "--host", dest="host", type="string", default="localhost", help="the STOMP server")
        p.add_option("-p", "--port", dest="port", type="int", default=61613, help="the STOMP port")
        p.add_option("-b", "--backend", dest="backend", type="string", default="xen", help="the backend to be used")
        p.add_option("-s", "--spool", dest="spool", type="string", default="/srv/xen-images/xenbee", help="the spool directory to use")
        p.add_option("-l", "--logfile", dest="logfile", type="string", default="/var/log/xenbee/xbed.log", help="the logfile to use")

        self.opts, self.args = p.parse_args(self.argv)
        global xenbeed
        try:
            xenbeed.initLogging(self.opts.logfile)
        except IOError, ioe:
            print >>sys.stderr, "E:", ioe
            sys.exit(1)
        
        log.info("initializing the `%s' backend" % self.opts.backend)
        import xenbeed.backend
        xenbeed.backend.initBackend(self.opts.backend)
        
        from xenbeed.instance import InstanceManager
        from xenbeed.task import TaskManager
        from xenbeed.scheduler import Scheduler
        
        self.instanceManager = InstanceManager(self.opts.spool)
        self.taskManager = TaskManager(self.instanceManager, self.opts.spool)
        self.scheduler = Scheduler(self.instanceManager, self.taskManager)
        
    def run(self, daemonize=False):
	""""""
	log.info("starting the XenBEE daemon")
        
        # connect to stomp server
        reactor.connectTCP(self.opts.host,
                           self.opts.port,
                           XenBEEProtocolFactory(self.scheduler,
                                                 queue="/queue/xenbee.daemon"))
        reactor.exitcode = 0
        reactor.run()
        return reactor.exitcode

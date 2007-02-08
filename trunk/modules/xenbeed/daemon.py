"""
The XenBee daemon.
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import xenbeed

import logging
log = logging.getLogger(__name__)

import sys, os.path

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
        
        log.info("initializing the `%s' backend..." % self.opts.backend)
        import xenbeed.backend
        xenbeed.backend.initBackend(self.opts.backend)
        log.info("  done.")
        
        log.info("initializing the file cache...")
        from xenbeed.cache import Cache
        self.cache = Cache(os.path.join(self.opts.spool, "cache"))
        log.info("  done.")

        log.info("initializing instance manager...")
        from xenbeed.instance import InstanceManager
        self.instanceManager = InstanceManager()
        log.info("  done.")

        log.info("initializing task manager...")
        from xenbeed.task import TaskManager
        self.taskManager = TaskManager(self.instanceManager,
                                       self.cache,
                                       os.path.join(self.opts.spool, "tasks"))
        log.info("  done.")

        log.info("initializing scheduler...")
        from xenbeed.scheduler import Scheduler
        self.scheduler = Scheduler(self.taskManager)
        log.info("  done.")
        
    def run(self, daemonize=False):
	""""""
	log.info("starting up the XenBEE daemon")
        
        # connect to stomp server
        reactor.connectTCP(self.opts.host,
                           self.opts.port,
                           XenBEEProtocolFactory(self,
                                                 queue="/queue/xenbee.daemon"))
        reactor.exitcode = 0
        reactor.run()
        return reactor.exitcode

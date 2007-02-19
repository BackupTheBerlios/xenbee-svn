"""
The XenBee daemon.
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging
log = logging.getLogger(__name__)

import sys, os.path, os
from xbe.util.daemon import Daemon

class XBEDaemon(Daemon):
    def __init__(self, argv=sys.argv):
	"""Initializes the Daemon."""
        Daemon.__init__(self, pidfile="/var/run/xbed.pid", umask=0007, name="xbed", user="root", group="root")
        p = self.parser
        p.add_option(
            "-H", "--host", dest="host", type="string", default="localhost",
            help="the STOMP server")
        p.add_option(
            "-p", "--port", dest="port", type="int", default=61613,
            help="the STOMP port")
        p.add_option(
            "-b", "--backend", dest="backend", type="string", default="xen",
            help="the backend to be used")
        p.add_option(
            "-s", "--spool", dest="spool", type="string", default="/srv/xen-images/xenbee",
            help="the spool directory to use")
        p.add_option(
            "-l", "--logfile", dest="logfile", type="string", default="/var/log/xenbee/xbed.log",
            help="the logfile to use")
        p.add_option(
            "-D", "--no-daemonize", dest="daemonize", action="store_false", default=True,
            help="do not daemonize")
        p.add_option(
            "--pidfile", dest="pidfile", type="string", default="/var/run/xbed.pid",
            help="the pidfile to use")
        p.add_option(
            "--key", dest="p_key", type="string",
            help="path to the private key")
        p.add_option(
            "--x509", dest="x509", type="string",
            help="path to the x509 certificate")
        p.add_option(
            "--ca-cert", dest="ca_cert", type="string",
            help="path to the CA x509 certificate")

    def configure(self):
        self.daemonize = self.opts.daemonize
        self.pidfile = self.opts.pidfile

        if self.opts.x509 is None:
            self.opts.x509 = os.path.join(os.environ["XBED_HOME"],
                                          "etc", "xbed", "xbed.pem")
        if self.opts.p_key is None:
            self.opts.p_key = os.path.join(os.environ["XBED_HOME"],
                                           "etc", "xbed", "private", "xbed-key.pem")
        if self.opts.ca_cert is None:
            self.opts.ca_cert = os.path.join(os.environ["XBED_HOME"],
                                             "etc", "CA", "ca-cert.pem")

    def setup_logging(self):
        import xbe
        try:
            xbe.initLogging(self.opts.logfile)
            self.log_error = log.fatal
        except IOError, ioe:
            raise Exception("%s: %s" % (ioe.strerror, ioe.filename))

    def setup_priviledged(self):
	log.info("Setting up the XenBEE daemon")

        log.info("initializing certificates...")
        # read in the certificate and private-key
        from xbe.xml.security import X509Certificate
        self.ca_certificate = X509Certificate.load_from_files(self.opts.ca_cert)
        subj_comp = dict([ c.split("=", 1) for c in self.ca_certificate.subject().split(", ")])
        log.info("   CA certificate: %s" % (subj_comp["CN"]))

        cert = X509Certificate.load_from_files(self.opts.x509,
                                               self.opts.p_key)
        if not self.ca_certificate.validate_certificate(cert):
            self.error("the given x509 certificate has not been signed by the given CA")
        self.certificate = cert
        subj_comp = dict([ c.split("=", 1) for c in self.certificate.subject().split(", ")])
        log.info("   my certificate: %s" % (subj_comp["CN"]))
        log.info("  done.")

        log.info("initializing twisted...")
        from twisted.python import threadable
        threadable.init()
        log.info("  done.")
        
        log.info("initializing the `%s' backend..." % self.opts.backend)
        import xbe.xbed.backend
        xbe.xbed.backend.initBackend(self.opts.backend)
        log.info("  done.")
        
        log.info("initializing the file cache...")
        from xbe.cached.cache import Cache
        self.cache = Cache(os.path.join(self.opts.spool, "cache"))
        self.cache.initializeDatabase().addErrback(str).addCallback(self.error)
        log.info("  done.")

        log.info("initializing instance manager...")
        from xbe.xbed.instance import InstanceManager
        self.instanceManager = InstanceManager(self.cache)
        log.info("  done.")

        log.info("initializing task manager...")
        from xbe.xbed.task import TaskManager
        self.taskManager = TaskManager(self.instanceManager,
                                            os.path.join(self.opts.spool, "tasks"))
        log.info("  done.")

        log.info("initializing scheduler...")
        from xbe.xbed.scheduler import Scheduler
        self.scheduler = Scheduler(self.taskManager)
        log.info("  done.")

        log.info("initializing login portal...")
        from twisted.cred.portal import Portal
        from twisted.cred.checkers import FilePasswordDB
        self.portal = Portal(realm=None)
#        checker = FilePasswordDB("/root/xenbee/etc/passwd")
#        self.portal.registerChecker(checker)

        from twisted.internet import reactor
        from xbe.xbed.proto import XenBEEDaemonProtocolFactory

        log.info("initializing reactor...")
        reactor.connectTCP(self.opts.host,
                           self.opts.port,
                           XenBEEDaemonProtocolFactory(self,
                                                       queue="/queue/xenbee.daemon"))
        log.info("  done.")
        
    def run(self, *args, **kw):
	""""""
        from twisted.internet import reactor
        reactor.exitcode = 0
        reactor.run()
        return reactor.exitcode

def main(argv):
    XBEDaemon().main(argv)

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
            "-c", "--config", dest="config", type="string",
            default=os.path.join(os.environ.get("XBED_HOME", "/"), "etc", "xbed", "xbedrc"),
            help="config file to use, default: %default")
        p.add_option(
            "-u", "--uri", dest="uri", type="string",
            help="the uri through which I'am reachable")
        p.add_option(
            "-U", "--user-database", dest="user_db", type="string",
            help="list CNs that are allowed to use this server")
        p.add_option(
            "-b", "--backend", dest="backend", type="string",
            help="the backend to be used")
        p.add_option(
            "-s", "--spool", dest="spool", type="string",
            help="the spool directory to use")
        p.add_option(
            "-S", "--schema-dir", dest="schema_dir", type="string",
            help="path to a directory where schema definitions can be found.")
        p.add_option(
            "-l", "--logfile", dest="log_file", type="string",
            help="the logfile to use")
        p.add_option(
            "-L", "--logconf", dest="log_conf", type="string",
            help="configuration file for the logging module")
        p.add_option(
            "-D", "--no-daemonize", dest="daemonize", action="store_false",
            default=True,
            help="do not daemonize")
        p.add_option(
            "-j", "--jail-package", dest="jail_package",
            help="path to a tar.bz2 that contains a jail hierarchy")
        p.add_option(
            "--pidfile", dest="pidfile", type="string",
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
        p.add_option(
            "--mac-file", dest="mac_file", type="string",
            help="path to a file, that contains available mac addresses "+
                 "paired with IP addresses.")
        p.add_option(
            "--stomp-user", dest="stomp_user", type="string",
            help="username for the stomp connection")
        p.add_option(
            "--stomp-pass", dest="stomp_pass", type="string",
            help="password for the stomp connection")
        try:
            import optcomplete
        except ImportError:
            # no optcompletion available
            pass
        else:
            optcomplete.autocomplete(p)

    def configure(self):
        self.daemonize = self.opts.daemonize
        from ConfigParser import ConfigParser
        cp = ConfigParser()
        read_files = cp.read([ "/etc/xbed/xbedrc",
                               os.path.expanduser("~/.xbed/xbedrc"),
                               self.opts.config])
        if not len(read_files):
            raise RuntimeError("no configuration file found")
        
        if self.opts.pidfile is not None:
            self.pidfile = self.opts.pidfile
        elif cp.has_option("global", "pidfile"):
            self.pidfile = cp.get("global", "pidfile")
        else:
            self.pidfile = "/var/run/xbed.pid"

        if self.opts.backend is None:
            self.opts.backend = cp.get("global", "backend")
        if self.opts.schema_dir is None:
            self.opts.schema_dir = cp.get("global", "schema_dir")
        if self.opts.spool is None:
            self.opts.spool = cp.get("global", "spool")

        if self.opts.log_conf is None:
            self.opts.log_conf = cp.get("logging", "logconf")
        if self.opts.log_conf is None and self.opts.log_file is None:
            self.opts.log_file = cp.get("logging", "logfile")

        if self.opts.uri is None:
            self.opts.uri = cp.get("stomp", "uri")
        if self.opts.stomp_user is None:
            self.opts.stomp_user = cp.get("stomp", "user")
        if self.opts.stomp_pass is None:
            self.opts.stomp_pass = cp.get("stomp", "pass")

        if self.opts.x509 is None:
            self.opts.x509 = cp.get("security", "pubkey")
        if self.opts.p_key is None:
            self.opts.p_key = cp.get("security", "privkey")
        if self.opts.ca_cert is None:
            self.opts.ca_cert = cp.get("security", "cacert")
        if self.opts.user_db is None:
            self.opts.user_db = cp.get("security", "userdb")

        if self.opts.mac_file is None:
            self.opts.mac_file = cp.get("instance", "macdb")
        if self.opts.jail_package is None:
            self.opts.jail_package = cp.get("instance", "jailpkg")

    def setup_logging(self):
        try:
            if os.path.exists(self.opts.log_conf):
                # try to use the logconf file
                from logging.config import fileConfig
                fileConfig(self.opts.log_conf)
                logging.currentframe = lambda: sys._getframe(3)
            else:
                import xbe
                # fall back and use a simple logfile
                xbe.initLogging(self.opts.log_file)
        except IOError, ioe:
            raise Exception("%s: %s" % (ioe.strerror, ioe.filename))
        global log
        log = logging.getLogger()
        log.info("logging has been set up")
        self.log_error = log.fatal
        
    def setup_priviledged(self):
	log.info("Setting up the XenBEE daemon")

        log.info("initializing schema documents...")
        from lxml import etree
        self.schema_map = {}
        for schema in os.listdir(self.opts.schema_dir):
            if not schema.endswith(".xsd"): continue
            path = os.path.join(self.opts.schema_dir, schema)
            log.info("   reading %s" % path)
            xsd_doc = etree.parse(path)
            namespace = xsd_doc.getroot().attrib["targetNamespace"]
            self.schema_map[namespace] = etree.XMLSchema(xsd_doc)
        log.info("  done.")
        
        log.info("initializing certificates...")
        # read in the certificate and private-key
        from xbe.xml.security import X509Certificate
        self.ca_certificate = X509Certificate.load_from_files(self.opts.ca_cert)
        log.info("   CA certificate: %s", self.ca_certificate.subject()["CN"])

        cert = X509Certificate.load_from_files(self.opts.x509,
                                               self.opts.p_key)
        if not self.ca_certificate.validate_certificate(cert):
            self.error("the given x509 certificate has not been signed by the given CA")
        self.certificate = cert
        log.info("   my certificate: %s" % (self.certificate.subject()["CN"]))
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
        self.cache.initialize().addBoth(str).addErrback(self.error)
        log.info("  done.")

        log.info("initializing mac address pool...")
        from xbe.xbed.resource import MacIPAddressPool
        self.macAddresses = MacIPAddressPool.from_file(self.opts.mac_file)
        log.info("  done.")

        log.info("initializing instance manager...")
        from xbe.xbed.instance import InstanceManager
        self.instanceManager = InstanceManager.getInstance(self)
        log.info("  done.")

        log.info("initializing task manager...")
        from xbe.xbed.task import TaskManager
        self.taskManager = TaskManager.getInstance(self.instanceManager,
                                                   os.path.join(self.opts.spool, "tasks"))
        log.info("  done.")

        log.info("initializing user database...")
        from xbe.xbed.user import UserDatabase
        self.userDatabase = UserDatabase.getInstance(self.opts.user_db)
        log.info("  done.")

        log.info("initializing reactor...")
        from twisted.internet import reactor
        from xbe.xbed.proto import XenBEEDaemonProtocolFactory

        from xbe.util.network import urlparse
        proto, host, queue, _, _, _ = urlparse(self.opts.uri)
        if proto != "stomp":
            raise ValueError("unknown protocol", proto)
        try:
            host, port = host.split(":")
            port = int(port)
        except ValueError, e:
            port = 61613
        log.info(" connecting to %s:%d using %s" % (
            host, port, proto
        ))
                 
        reactor.connectTCP(host,
                           port,
                           XenBEEDaemonProtocolFactory(self,
                                                       queue="/queue"+queue,
                                                       topic="/topic/xenbee.daemons",
                                                       user=self.opts.stomp_user,
                                                       passwrd=self.opts.stomp_pass))
        log.info("  done.")
        
    def run(self, *args, **kw):
	""""""
        from twisted.internet import reactor
        reactor.exitcode = 0
        reactor.run()
        return reactor.exitcode

def main(argv):
    XBEDaemon.getInstance().main(argv)

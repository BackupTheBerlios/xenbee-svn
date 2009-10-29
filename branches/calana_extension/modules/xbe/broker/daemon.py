# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA

"""
The Calana Broker daemon.
"""

__version__ = "$Rev: 462 $"
__author__ = "$Author: krueger $"

import logging
log = logging.getLogger(__name__)

import sys, os.path, os
from xbe.util.daemon import Daemon

class CalanaBrokerDaemon(Daemon):
    def __init__(self, argv=sys.argv):
	"""Initializes the Daemon."""
        Daemon.__init__(self, pidfile="/var/run/xbebroker.pid", umask=0007, name="xbebroker", user="root", group="root")
        self.server_queue = "xenbee.daemon.1"
        
        p = self.parser
        p.add_option(
            "-c", "--config", dest="config", type="string",
            help="config file to use, default: %default")
        p.add_option(
            "-u", "--uri", dest="uri", type="string",
            help="the uri through which I'am reachable")
        p.add_option(
            "--server", dest="server", type="string",
            help="the server to connect to")
        p.add_option(
            "-U", "--user-database", dest="user_db", type="string",
            help="list CNs that are allowed to use this server")
        p.add_option(
            "--pidfile", dest="pidfile", type="string",
            help="the pidfile to use")
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
            "--key", dest="p_key", type="string",
            help="path to the private key")
        p.add_option(
            "--x509", dest="x509", type="string",
            help="path to the x509 certificate")
        p.add_option(
            "--ca-cert", dest="ca_cert", type="string",
            help="path to the CA x509 certificate")

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
        
        read_files = cp.read([ os.path.join(os.environ.get("XBED_HOME", "/"), "etc", "broker", "brokerrc"),
                               os.path.expanduser("~/.xbed/brokerrc"),
                               self.opts.config or ""])
        if not len(read_files):
            raise RuntimeError("no configuration file found")
        
        if self.opts.pidfile is not None:
            self.pidfile = self.opts.pidfile
        elif cp.has_option("global", "pidfile"):
            self.pidfile = os.path.expanduser(cp.get("global", "pidfile"))
        else:
            self.pidfile = "/var/run/xbebreoker.pid"

        if self.opts.schema_dir is None:
            self.opts.schema_dir = os.path.expanduser(cp.get("global", "schema_dir"))

        if self.opts.log_conf is None:
            self.opts.log_conf = os.path.expanduser(cp.get("logging", "logconf"))
        if self.opts.log_conf is None and self.opts.log_file is None:
            self.opts.log_file = os.path.expanduser(cp.get("logging", "logfile"))

        if self.opts.x509 is None:
            self.opts.x509 = os.path.expanduser(cp.get("security", "pubkey"))
        if self.opts.p_key is None:
            self.opts.p_key = os.path.expanduser(cp.get("security", "privkey"))
        if self.opts.ca_cert is None:
            self.opts.ca_cert = os.path.expanduser(cp.get("security", "cacert"))
        if self.opts.user_db is None:
            self.opts.user_db = os.path.expanduser(cp.get("security", "userdb"))

        if self.opts.uri is None:
            self.opts.uri = cp.get("network", "uri")
        if self.opts.server is None:
            self.opts.server = cp.get("network", "server")
        if self.opts.stomp_user is None:
            self.opts.stomp_user = cp.get("network", "user")
        if self.opts.stomp_pass is None:
            self.opts.stomp_pass = cp.get("network", "pass")

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
	log.info("Setting up the XenBEE broker")

# TODO: hier muss etwas rein!! - start
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
        
        log.info("initializing user database...")
        from xbe.xbed.user import UserDatabase
        self.userDatabase = UserDatabase.getInstance(self.opts.user_db)
        log.info("  done.")

        log.info("initializing reactor...")
        from twisted.internet import reactor
        from xbe.broker.proto import XenBEEBrokerProtocolFactory


        from xbe.util.network import urlparse
        proto, host, queue, _, _, _ = urlparse(self.opts.uri)
        if proto != "stomp":
            raise ValueError("unknown protocol", proto)
        try:
            host, port = host.split(":")
            port = int(port)
        except ValueError, e:
            port = 61613
	queue = queue.lstrip("/")
        log.info(" connecting to %s:%d using %s, queue: %s" % (
            host, port, proto, queue
        ))

        # todo move this stuff to the config and remove the old "uri" way
        self.broker = "tcp://%s:%d?wireFormat=%s&username=%s&password=%s" % (
            host, port, "stomp", self.opts.stomp_user, self.opts.stomp_pass
        )
        self.qname = queue
                 
        reactor.connectTCP(host,
                           port,
                           XenBEEBrokerProtocolFactory(self,
                                                       queue="/queue/"+queue,
                                                       topic="/queue/xenbee.daemons",
                                                       server_queue="/queue/"+self.server_queue,
                                                       user=self.opts.stomp_user,
                                                       password=self.opts.stomp_pass))
        log.info("  done.")

# TODO: hier muss etwas rein!!  - end


    def run(self, *args, **kw):
	""""""
	log.info("broker.run")
        from twisted.internet import reactor
        reactor.exitcode = 0
        reactor.run()
        return reactor.exitcode


##################################################
###    
##################################################
def main(argv):
    CalanaBrokerDaemon.getInstance().main(argv)

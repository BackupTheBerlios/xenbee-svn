"""
The XenBee instance daemon.
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import sys, logging, os, os.path
log = logging.getLogger(__name__)

from xbe.util.daemon import Daemon
from xbe.util.uuid import uuid

class XBEInstDaemon(Daemon):
    def __init__(self, argv=sys.argv):
        Daemon.__init__(self, pidfile="/var/run/xbeinstd.pid",
                        umask=0007, name="xbeinstd", user="root", group="root")
        p = self.parser
        p.add_option("-H", "--host", dest="server", type="string",
                     help="the server uri (stomp://host[:port]/queue)",
                     default=os.environ.get("XBE_SERVER"))
        p.add_option("-D", "--no-daemonize", dest="daemonize", action="store_false",
                      help="do not daemonize",
                     default=True)
        p.add_option("-S", "--schema-dir", dest="schema_dir", type="string",
                     help="path to a directory that contains schema documents",
                     default="/root/xenbee/etc/xml/schema")
        p.add_option("-l", "--logfile", dest="logfile", type="string",
                     help="the logfile to use",
                     default="/var/log/xenbee/xbeinstd.log")
        p.add_option("--pidfile", dest="pidfile", type="string",
                     help="the pidfile to use",
                     default="/var/run/xbeinstd.pid")
        p.add_option("-u", "--uuid", dest="uuid", type="string",
                     help="the uuid to use",
                     default=os.environ.get("XBE_UUID"))

    def configure(self):
        self.daemonize = self.opts.daemonize
        self.pidfile = self.opts.pidfile

    def setup_logging(self):
        # fix the 'currentframe' function in the logging module,
        # so that correct line numbers get logged:
        # see: http://sourceforge.net/tracker/index.php?func=detail&aid=1652788&group_id=5470&atid=105470
        logging.currentframe = lambda: sys._getframe(3)

        if sys.hexversion >= 0x2040200:
            # threadName available
            thread = ":%(threadName)s"
        else:
            thread = ""
        if not os.path.exists(os.path.dirname(self.opts.logfile)):
            os.makedirs(os.path.dirname(self.opts.logfile))

        _fileHdlr = logging.FileHandler(self.opts.logfile, 'w+b')
        _fileHdlr.setLevel(logging.DEBUG)
        _fileHdlr.setFormatter(logging.Formatter(
            '%(asctime)s [%(process)d]' + thread + ' %(name)s:%(lineno)d %(levelname)-8s %(message)s'))
        logging.getLogger().addHandler(_fileHdlr)

        logging.getLogger().setLevel(logging.DEBUG)
        self.log_error = log.fatal

    def setup_priviledged(self):
	log.info("Setting up the XenBEE instance daemon")

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
        
        log.info("initializing the twisted framework...")
        from twisted.python import threadable
        threadable.init()
        log.info("  done.")

        # set up the uuid
        if self.opts.uuid is None:
            raise RuntimeError("could not get my instance id")
        self.queue = "/queue/xenbee.instance.%s" % (self.opts.uuid)

        # set up the STOMP server
        from xbe.util.network import urlparse
        if self.opts.server is None:
            raise RuntimeError("no server uri given, use XBE_SERVER or -H")
        proto, host, queue, _, _, _ = urlparse(self.opts.server)
        if proto != "stomp":
            raise ValueError("unknown protocol", proto)
        try:
            self.host, port = host.split(":")
            self.port = int(port)
        except Exception, e:
            self.host = host
            self.port = 61613
            
        log.info("initializing reactor...")
        from twisted.internet import reactor
        from xbe.xbeinstd.protocol.instance import XenBEEInstProtocolFactory

        f = XenBEEInstProtocolFactory(self, self.opts.uuid,
                                      my_queue=self.queue, server_queue="/queue"+queue)
        reactor.connectTCP(self.host,
                           self.port,
                           f)
        log.info("  done.")
        
    def run(self, *args, **kw):
	""""""
        from twisted.internet import reactor
        reactor.exitcode = 0
        reactor.run()
        return reactor.exitcode

def main(argv):
    XBEInstDaemon.getInstance().main(argv)

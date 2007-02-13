"""
The XenBee instance daemon.
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import sys, logging, os, os.path
log = logging.getLogger(__name__)

from xbe.util.daemon import Daemon
from xbe.util.uuid import uuid
from twisted.python import threadable
threadable.init()
from twisted.internet import reactor

from xbe.xbeinstd.protocol.instance import XenBEEInstProtocolFactory

class XBEInstDaemon(Daemon):
    def __init__(self, argv=sys.argv):
        Daemon.__init__(self, pidfile="/var/run/xbeinstd.pid",
                        umask=0007, name="xbeinstd", user="root", group="root")
        p = self.parser
        p.add_option("-S", "--server", dest="server",
                     type="string", help="the STOMP server (host[:port])", default=os.environ.get("XBE_SERVER"))
        p.add_option("-D", "--no-daemonize", dest="daemonize", action="store_false", default=True, help="do not daemonize")
        p.add_option("-l", "--logfile", dest="logfile",
                     type="string", default="/var/log/xenbee/xbeinstd.log", help="the logfile to use")
        p.add_option("--pidfile", dest="pidfile",
                     type="string", default="/var/run/xbeinstd.pid", help="the pidfile to use")
        p.add_option("-u", "--uuid", dest="uuid",
                     type="string", default=os.environ.get("XBE_UUID"), help="the uuid to use")

    def __parseServer(self, server):
        if server is None:
            xbe_server, xbe_port = "localhost", 61613
            log.warn("running in local mode with server at %s:%d" % (xbe_server,xbe_port))
            return xbe_server, xbe_port

        try:
            xbe_server, xbe_port = server.split(":")
            xbe_port = int(xbe_port)
        except ValueError, ve:
            return server, 61613

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
	log.info("setting up the XenBEE instance daemon")
        
        # set up the uuid
        if self.opts.uuid is None:
            self.opts.uuid = uuid()
            log.warn("could not get my instance id, using: %s" % self.opts.uuid)
        self.queue = "/queue/xenbee.instance.%s" % (self.opts.uuid)

        # set up the STOMP server
        try:
            self.xbe_host, self.xbe_port = self.__parseServer(self.opts.server)
        except Exception, e:
            self.error("could not interpret server: %s" % self.opts.server)
        
        log.info("initializing reactor...")
        f = XenBEEInstProtocolFactory(self,
                                      my_queue=self.queue, server_queue="/queue/xenbee.daemon")
        f.instanceId = self.opts.uuid
        reactor.connectTCP(self.xbe_host,
                           self.xbe_port,
                           f)
            
        log.info("  done.")
        
    def run(self, *args, **kw):
	""""""
        reactor.exitcode = 0
        reactor.run()
        return reactor.exitcode

def main(argv):
    XBEInstDaemon().main(argv)

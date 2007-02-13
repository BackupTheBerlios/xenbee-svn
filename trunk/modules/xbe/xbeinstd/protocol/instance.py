"""The protocol spoken between the xbed and the instance-daemon."""

import logging
log = logging.getLogger(__name__)

from twisted.internet import reactor

from xbe.proto import XenBEEProtocolFactory, XenBEEProtocol
from xbe.xbeinstd.protocol.process import XBEProcessProtocol
from xbe.xml import xsdl

class XBEInstProtocol(xsdl.XMLProtocol):
    def __init__(self, transport):
        self.proc = None
        xsdl.XMLProtocol.__init__(self,transport)
        self.addUnderstood(xsdl.JSDL("JobDefinition"))

    def do_JobDefinition(self, job_def):
        desc = job_def.find(xsdl.JSDL("JobDescription"))

        j_name = desc.findtext(xsdl.JSDL("JobIdentification/JobName"))
        j_desc = desc.findtext(xsdl.JSDL("JobIdentification/Description"))

        app = job_def.find(xsdl.XSDL("InstanceDefinition/InstanceDescription") + "/" +
                           xsdl.JSDL("Application"))
        posixApp = app.find(xsdl.JSDL_POSIX("POSIXApplication"))
        executable = posixApp.findtext(xsdl.JSDL_POSIX("Executable"))
            
        args = [(n.text or "").strip() for n in posixApp.findall(xsdl.JSDL_POSIX("Argument"))]
        cmdline = [ executable ]
        cmdline.extend(args)
        log.info("executing task: " + `cmdline`)

        self.proc = XBEProcessProtocol(self)
        self.proc.cmdline = cmdline
        reactor.spawnProcess(self.proc, cmdline[0], cmdline, {})

    # process handling callbacks
    def processEnded(self, status_object):
        msg = xsdl.XenBEEClientMessage()
        tsn = msg.createElement("TaskStatusNotification", msg.root)
        tf = msg.createElement("TaskFinished", tsn)
        msg.createElement("ExitCode", tf, str(status_object.value.exitCode))
        msg.createElement("CommandLine", tf, str(self.proc.cmdline))

        def listToString(_list):
            return "".join(map(str, _list))
        stdOutput, errOutput = map(listToString, [self.proc.stdOutput, self.proc.errOutput])
        msg.createElement("StandardOutput", tf, stdOutput)
        msg.createElement("ErrorOutput", tf, errOutput)
        self.proc = None
        self.transport.write(str(msg))

        log.info("process ended: code:%d\nout:'%s'\nerr:'%s'" % (status_object.value.exitCode, stdOutput, errOutput))

class _InstProtocol(XenBEEProtocol):
    def _discover_ips(self):
        # since we were able to connect to the STOMP server, we simply
        # connect here a second time ;-)  but this time we just use it
        # to discover our own ips:
        import socket

        ips = []
        for family, desc in [ (socket.AF_INET6, "ipv6"),
                              (socket.AF_INET, "ipv4")]:
            log.info("trying %s..." % desc)

            s = socket.socket(family, socket.SOCK_STREAM)

            s.bind(('', 0)) # bind to all interfaces, arbitrary port

            # now connect the socket to our STOMP server
            try:
                stompServer = (self.factory.daemon.xbe_host,
                               self.factory.daemon.xbe_port)
                s.connect(stompServer)
            except (socket.gaierror, socket.error), e:
                log.info("could not connect to %s:%d" % (stompServer))
                continue
                
            # connect was successful, now get the needed information from the socket
            sock_nam = s.getsockname()
            ips.append(sock_nam[0])

            s.close()
            del s
            break

        # for each discovered ip, resolve it to a fqdn
        fqdns = {}
        for ip in ips:
            try:
                hostname, aliaslist, ipaddrlist = socket.gethostbyaddr(ip)
                info = fqdns.get(hostname, [])
                info.extend(ipaddrlist)
                fqdns[hostname] = info
            except socket.herror:
                pass
        return fqdns
    
    def post_connect(self):
        log.info("notifying xbe daemon, that i am available now")
        try:
            msg = xsdl.XenBEEInstanceAvailable(self.factory.instanceId)
            try:
                fqdn, ips = self._discover_ips().popitem()
                # simply take random one
                msg.setNetworkInfo(fqdn, ips)
            except Exception, e:
                log.error("could not discover my ips: %s", e)
                msg.setNetworkInfo('n/a', [])
            self.send(self.factory.server_queue, str(msg))
        except Exception, e:
            log.exception("send failed: %s" % e)
            raise

class XenBEEInstProtocolFactory(XenBEEProtocolFactory):
    protocol = _InstProtocol
    
    def __init__(self, daemon, my_queue, server_queue):
	XenBEEProtocolFactory.__init__(self, daemon, my_queue)
        self.p = None
        self.server_queue = server_queue
        self.daemon = daemon

    def dispatchToProtocol(self, transport, msg, domain, sourceType, sourceId=None):
        if domain != "xenbee":
            raise ValueError("illegal domain: %s, expected 'xenbee'" % domain)
        if sourceType != "daemon":
            raise ValueError("illegal source type: %s, expected 'daemon'" % sourceType)
        if not self.p:
            self.p = XBEInstProtocol(transport)
        self.p.messageReceived(msg)

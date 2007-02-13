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
    def post_connect(self):
        log.info("notifying xbe daemon, that i am available now")
        try:
            msg = xsdl.XenBEEInstanceAvailable(self.factory.instanceId)

            # get my IP
            from socket import gethostbyaddr, gethostname
            try:
                fqdn, _, ips = gethostbyaddr(gethostname())
            except Exception, e:
                log.exception(e)
                fqdn, ips = "N/A", []
            msg.setNetworkInfo(fqdn, ips)

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

    def dispatchToProtocol(self, transport, msg, domain, sourceType, sourceId=None):
        if domain != "xenbee":
            raise ValueError("illegal domain: %s, expected 'xenbee'" % domain)
        if sourceType != "daemon":
            raise ValueError("illegal source type: %s, expected 'daemon'" % sourceType)
        if not self.p:
            self.p = XBEInstProtocol(transport)
        self.p.messageReceived(msg)

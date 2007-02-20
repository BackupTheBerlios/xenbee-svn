"""The protocol spoken between the xbed and the instance-daemon."""

import logging
log = logging.getLogger(__name__)

from twisted.internet import reactor

from xbe.util.network import discover_ips
from xbe.proto import XenBEEProtocolFactory, XenBEEProtocol
from xbe.xbeinstd.protocol.process import XBEProcessProtocol
from xbe.xml import message, errcode, protocol as xmlprotocol
from xbe.xml.namespaces import *

class XBEInstProtocol(xmlprotocol.XMLProtocol):
    def __init__(self):
        xmlprotocol.XMLProtocol.__init__(self)
        self.proc = None

    def connectionMade(self):
        # send instance available message
        log.info("notifying xbe daemon, that i am available now")
        try:
            msg = message.InstanceAvailable(self.factory.instance_id)
            try:
                stompServer = (self.factory.daemon.xbe_host,
                               self.factory.daemon.xbe_port)
                
                # discover our ips and add to the message
                map(msg.add_ip, discover_ips(stompServer))
            except Exception, e:
                log.error("could not discover my ip: %s", e)
            self.sendMessage(self.transformResultToMessage(msg))
        except Exception, e:
            log.exception("send failed: %s" % e)
            raise

        # schedule 'alive' timer-task
        log.warn("TODO: schedule InstanceAlive timer-task")

    def do_JobDefinition(self, job_def):
        if self.proc is not None:
            # there is already a job running right now
            return message.Error(errcode.JOB_ALREADY_RUNNING)
        
        desc = job_def.find(JSDL("JobDescription"))

        j_name = desc.findtext(JSDL("JobIdentification/JobName"))
        j_desc = desc.findtext(JSDL("JobIdentification/Description"))

        app = job_def.find(XSDL("InstanceDefinition/InstanceDescription") + "/" +
                           JSDL("Application"))
        posixApp = app.find(JSDL_POSIX("POSIXApplication"))
        executable = posixApp.findtext(JSDL_POSIX("Executable"))
            
        args = [(n.text or "").strip() for n in posixApp.findall(JSDL_POSIX("Argument"))]
        cmdline = [ executable ]
        cmdline.extend(args)
        log.info("executing task: " + `cmdline`)

        self.proc = XBEProcessProtocol(self)
        self.proc.cmdline = cmdline
        reactor.spawnProcess(self.proc, cmdline[0], cmdline, {})

    # process handling callbacks
    def processEnded(self, status_object):
        log.info("process ended: code:%d\nout:'%s'\nerr:'%s'" % (status_object.value.exitCode,
                                                                 stdOutput, errOutput))
        msg = message.TaskFinished(
            inst_id=self.factory.instance_id,
            exitcode=status_object.value.exitCode)
        self.sendMessage(self.transformResultToMessage(msg))
        del self.proc

#        def listToString(_list):
#            return "".join(map(str, _list))
#        stdOutput, errOutput = map(listToString, [self.proc.stdOutput, self.proc.errOutput])
#        msg.createElement("StandardOutput", tf, stdOutput)
#        msg.createElement("ErrorOutput", tf, errOutput)
#        self.proc = None
#        self.transport.write(str(msg))


class _InstProtocol(XenBEEProtocol):
    
    def post_connect(self):
        self.factory.stompConnectionMade()

class XenBEEInstProtocolFactory(XenBEEProtocolFactory):
    protocol = _InstProtocol
    
    def __init__(self, daemon, instance_id, my_queue, server_queue):
	XenBEEProtocolFactory.__init__(self, daemon, my_queue)
        self.instance_id = instance_id
        self.p = None
        self.server_queue = server_queue
        self.daemon = daemon

    def dispatchToProtocol(self, transport, msg, domain, sourceType, sourceId=None):
        self.p.messageReceived(msg)

    def stompConnectionMade(self, stomp_protocol):
        if self.p is None:
            self.p = XBEInstProtocol()
            self.p.factory = self
            self.p.makeConnection(xmlprotocol.XMLTransport(
                StompTransport(self.server_queue, stomp_protocol)))


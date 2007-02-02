#!/usr/bin/env python
"""
The Xen Based Execution Environment protocol
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

import logging
log = logging.getLogger(__name__)

from stomp.proto import StompClient, StompClientFactory, StompTransport
from xenbeed import isdl

# Twisted imports
from twisted.internet import reactor
import threading

class XenBEEClientProtocol(isdl.XMLProtocol):
    """The XBE client side protocol.

    This protocol is spoken between some client (user, script
    etc.). The protocol is based on XML
    """

    def __init__(self, client, transport):
        isdl.XMLProtocol.__init__(self, transport)
        self.client = client
        self.addUnderstood("ImageSubmission", isdl.ISDL_NS)
        self.addUnderstood("StatusRequest", isdl.ISDL_NS)
        self.addUnderstood("Kill", isdl.ISDL_NS)

    def do_ImageSubmission(self, elem):
	"""Handle an image submission."""

        # run some checks on the received document
	imgDef = elem.find(isdl.Tag("ImageDefinition", isdl.ISDL_NS))
	if not imgDef:
	    raise Exception("no ImageDefinition found.")

        # create a new task object for this submission
        task = self.factory.taskManager.newTask(elem)

    def do_StatusRequest(self, dom_node):
	"""Handle status request."""
        msg = isdl.XenBEEStatusMessage()
        map(msg.addStatusForInstance, self.factory.instanceManager)
        self.transport.write(str(msg))

    def do_Kill(self, node):
        # get the signal type
        sig = isdl.getChild(node, "Signal")
        if not sig:
            self.transport.write(            
                str(isdl.XenBEEClientError("no signal given!",
                                           isdl.XenBEEClientError.ILLEGAL_REQUEST))
                )
            return
        
        try:
            signum = int(sig.text)
            if not signum in [ 9, 15 ]:
                raise ValueError("out of range, allowed are (9,15)")
        except Exception, e:
            self.transport.write(
                str(isdl.XenBEEClientError("Illegal signal: %s" % (e,),
                                           isdl.XenBEEClientError.ILLEGAL_REQUEST))
                )
            raise

        for t in node.findall(isdl.Tag("JobID")):
            instID = t.text.strip()
            inst = self.factory.instanceManager.lookupByUUID(instID)
            
            if not inst:
                self.transport.write(            
                    str(isdl.XenBEEClientError("no such job: %s" % (instID,),
                                               isdl.XenBEEClientError.ILLEGAL_REQUEST))
                    )
            inst.stop()
        self.transport.write(str(isdl.XenBEEClientError("signal sent", isdl.XenBEEClientError.OK)))
	
class XenBEEInstanceProtocol(isdl.XMLProtocol):
    """The XBE instance side protocol.

    This protocol is spoken between an instance and the daemon.
    """

    def __init__(self, instid, transport):
        isdl.XMLProtocol.__init__(self, transport)
	self.instid = instid
        self.addUnderstood("InstanceAvailable", isdl.ISDL_NS)
        self.addUnderstood("TaskStatusNotification", isdl.ISDL_NS)
        
    def do_InstanceAvailable(self, dom_node):
        inst_id = isdl.getChild(dom_node, "InstanceID").text.strip()
        inst = self.factory.instanceManager.lookupByUUID(inst_id)
        if not inst:
            raise ValueError("no such instance")
        
#        isdlDoc = inst._isdlDocument
#        jsdlPart = isdl.getChild(isdlDoc, "JobDefinition", isdl.JSDL_NS)
#        if not jsdlPart:
#            raise ValueError("no JobDefinition found!")
#        jsdlPrefix = jsdlPart.prefix
#
#        jsdlPosixPart = isdl.getChild(jsdlPart, "POSIXApplication", isdl.JSDL_POSIX_NS)
#        jsdlPosixPrefix = jsdlPosixPart.prefix
#
#        # build task submission
#        msg = isdl.XenBEEClientMessage()
#        msg.addNamespace(jsdlPrefix, isdl.JSDL_NS).addNamespace(jsdlPosixPrefix, isdl.JSDL_POSIX_NS)
#        msg.root.appendChild(jsdlPart.cloneNode(True))
#        
#        log.info("instance is now managable: %s" % inst_id)
#        log.debug("submitting:\n%s" % str(msg))
#        self.transport.write(str(msg))

    def do_TaskStatusNotification(self, status_node):
        fin_node = isdl.getChild(status_node, "TaskFinished")
        exitcode = int(isdl.getChild(fin_node, "ExitCode").text)
        errout   = isdl.getChild(fin_node, "ErrorOutput").text
        log.info("task finished: code=%d errout='%s'" % (exitcode, errout))

class XenBEEProtocol(StompClient):
    """Processing input received by the STOMP server."""

    def __init__(self):
	self.factory = None
	StompClient.__init__(self)

    def connectedReceived(self, _):
	self.factory.stomp = self
	# i am connected to the stomp server
	log.debug("successfully connected to STOMP server, avaiting your commands.")
        self.setReplyTo(self.factory.queue)
	self.subscribe(self.factory.queue, auto_ack=True)
        self.subscribe('/topic/ActiveMQ.Advisory.Consumer.Queue.>')

    def _advisoryReceived(self, msg):
        return
    
    def _messageReceived(self, msg):
        # check if we got an advisory from the activemq server
        if msg.header.get("type", "no") == "Advisory":
            return self._advisoryReceived(msg)
        log.debug("got message:\n%s" % (str(msg),))

        # use the reply-to field
        try:
            replyTo = msg.header["reply-to"]
        except KeyError:
	    log.warn("illegal message received")
            raise

        momIdentifier = replyTo.replace("/queue/", "")
        domain, clientType, clientId = momIdentifier.split(".", 2)
        if domain != "xenbee":
            raise ValueError("wrong subqueue: "+str(domain))
        if clientType == "client":
	    # request from some client
	    self.factory.newClient(msg, clientId, replyTo)
	elif clientType == "instance":
	    # message from an instance
	    self.factory.newInstance(msg, clientId, replyTo)
	else:
            log.warn("illegal client type: %s" % clientType)
            
    def messageReceived(self, msg):
        try:
            return self._messageReceived(msg)
        except:
            log.exception("message handling failed")

    def errorOccured(self, msg, detail):
	log.error("error-message: '%s', details: '%s'" % (msg, detail))

class XenBEEProtocolFactory(StompClientFactory):
    protocol = XenBEEProtocol

    def __init__(self, scheduler, queue="/queue/xenbee.daemon"):
	StompClientFactory.__init__(self, user='daemon', password='none')
	self.queue = queue
	self.stomp = None
        self.scheduler = scheduler
	self.instanceManager = scheduler.instanceManager
        self.taskManager = scheduler.taskManager

    def clientConnectionFailed(self, connector, reason):
	log.error("connection to STOMP server failed!: %s" % (str(reason.value)))
	if 'twisted.internet.error.ConnectionRefusedError' in reason.parents:
            log.info("shutting the server down...")
            reactor.exitcode = 1
            reactor.stop()
	else:
	    StompClientFactory.clientConnectionFailed(self, connector, reason)

    def newClient(self, msg, client, replyto):
	clientProtocol = XenBEEClientProtocol(client, StompTransport(self.stomp, replyto))
	clientProtocol.factory = self
        reactor.callInThread(clientProtocol.messageReceived, msg)

    def newInstance(self, msg, instId, replyto):
        instProtocol = XenBEEInstanceProtocol(instId, StompTransport(self.stomp, replyto))
	instProtocol.factory = self
        reactor.callInThread(instProtocol.messageReceived, msg)

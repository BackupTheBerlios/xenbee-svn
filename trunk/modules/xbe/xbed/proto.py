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
from lxml import etree

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
        self.addUnderstood(isdl.Tag("ImageSubmission"))
        self.addUnderstood(isdl.Tag("StatusRequest"))
        self.addUnderstood(isdl.Tag("Kill"))
        self.addUnderstood(isdl.Tag("ListCache"))

    def do_ImageSubmission(self, elem):
	"""Handle an image submission."""
        # run some checks on the received document
	imgDef = elem.find(isdl.ISDL("ImageDefinition"))
	if not imgDef:
	    raise Exception("no ImageDefinition found.")

        # create a new task object for this submission
        task = self.factory.taskManager.newTask(elem)
        self.transport.write(
            str(isdl.XenBEEClientError("task submitted: %s" % task.ID(),
                                       isdl.XenBEEClientError.OK))
            )

    def do_StatusRequest(self, dom_node):
	"""Handle status request."""
        msg = isdl.XenBEEStatusMessage()
        map(msg.addStatusForTask, self.factory.taskManager.tasks.values())
        self.transport.write(str(msg))

    def do_Kill(self, elem):
        sig = int(elem.findtext(isdl.ISDL("Signal")))
        if not sig in [ 9, 15 ]:
            raise ValueError("out of range, allowed are (9,15)")
        for tid in map(lambda t: (t.text or "").strip(), elem.findall(isdl.ISDL("JobID"))):
            task = self.factory.taskManager.lookupByID(tid)
            if not task:
                self.transport.write(            
                    str(isdl.XenBEEClientError("no such task: %s" % (tid,),
                                               isdl.XenBEEClientError.ILLEGAL_REQUEST))
                    )
            else:
                task.kill(sig)
        self.transport.write(
            str(isdl.XenBEEClientError("signal sent", isdl.XenBEEClientError.OK)))

    def do_ListCache(self, elem):
        def __sendMessage(entries):
            msg = isdl.XenBEECacheEntries()
            for uid, type, desc in entries:
                msg.addEntry(uid, type, desc)
            self.transport.write(str(msg))
        self.factory.cache.getEntries().addCallback(__sendMessage)
	
class XenBEEInstanceProtocol(isdl.XMLProtocol):
    """The XBE instance side protocol.

    This protocol is spoken between an instance and the daemon.
    """

    def __init__(self, instid, transport):
        isdl.XMLProtocol.__init__(self, transport)
	self.instid = instid
        self.addUnderstood(isdl.Tag("InstanceAvailable"))
        self.addUnderstood(isdl.Tag("TaskStatusNotification"))

    def executeTask(self, task):
        job = task.document.find("./" + isdl.JSDL("JobDefinition"))
        if job == None:
            raise RuntimeError("no job definition found for task %s" % (task.ID()))
        msg = isdl.XenBEEClientMessage()
        msg.root.append(etree.fromstring(etree.tostring(job)))

        log.info("submitting:\n%s" % str(msg))
        self.transport.write(str(msg))

    def queryStatus(self):
        pass

    #########################
    #                       #
    # Message handling part #
    #                       #
    #########################
    def do_InstanceAvailable(self, dom_node):
        inst_id = isdl.getChild(dom_node, "InstanceID").text.strip()
        if inst_id != self.instid:
            raise ValueError("got answer from different instance!")
        inst = self.factory.instanceManager.lookupByUUID(inst_id)
        if not inst:
            raise ValueError("no such instance")
        if inst.task == None:
            raise ValueError("no task belongs to this instance")
        inst.protocol = self
        inst.available()

    def do_TaskStatusNotification(self, status_elem):
        fin_elem = isdl.getChild(status_elem, "TaskFinished")
        exitcode = int(isdl.getChild(fin_elem, "ExitCode").text)
        errout   = isdl.getChild(fin_elem, "ErrorOutput").text
        log.info("task finished: code=%d errout='%s'" % (exitcode, errout))

        task = self.factory.instanceManager.lookupByUUID(self.instid).task
        task.status_elem = status_elem
        task.finished(exitcode)

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

    def __init__(self, daemon, queue="/queue/xenbee.daemon"):
	StompClientFactory.__init__(self, user='daemon', password='none')
	self.queue = queue
	self.stomp = None
        self.daemon = daemon
	self.instanceManager = daemon.instanceManager
        self.taskManager = daemon.taskManager
        self.cache = daemon.cache

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

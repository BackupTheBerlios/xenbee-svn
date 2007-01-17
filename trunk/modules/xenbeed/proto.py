#!/usr/bin/env python
"""
The Xen Based Execution Environment protocol
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

import logging
log = logging.getLogger(__name__)

from stomp.proto import StompClient, StompClientFactory, StompTransport
from xenbeed.instance import InstanceManager
from xenbeed import isdl

# Twisted imports
from twisted.internet import reactor

import xml.dom, threading
from xml.dom.ext.reader import PyExpat as XMLReaderBuilder

class XenBEEClientProtocol(isdl.XMLProtocol):
    """The XBE client side protocol.

    This protocol is spoken between some client (user, script
    etc.). The protocol is based on XML
    """

    def __init__(self, client, transport):
        isdl.XMLProtocol.__init__(self, transport)
	self.client = client

    def do_ImageSubmission(self, dom_node):
	"""Handle an image submission."""
	# parse image information and start retrieval of neccessary files
	imgDefNode = isdl.getChild(dom_node, "ImageDefinition")
	if not imgDefNode:
	    raise Exception("no ImageDefinition found.")

	# boot block
	bootNode = isdl.getChild(imgDefNode, "Boot")
	files = {}
	files["kernel"] = isdl.getChild(
	    isdl.getChild(bootNode, "Kernel"), "URI").firstChild.nodeValue.strip()
	files["initrd"] = isdl.getChild(
	    isdl.getChild(bootNode, "Initrd"), "URI").firstChild.nodeValue.strip()

	# image block
	imagesNode = isdl.getChild(imgDefNode, "Images")

	bootImageNode = isdl.getChild(imagesNode, "BootImage")
	files["root"] = isdl.getChild(
	    isdl.getChild(bootImageNode, "Source"), "URI").firstChild.nodeValue.strip()
	log.debug(files)

	# create instance and add files
	inst = self.factory.instanceManager.newInstance()
	d = inst.addFiles(files)

        def handleSuccess(_):
            pass
        def _errFunc(err):
            self.transport.write(            
                str(isdl.XenBEEClientError("file retrieval failed " + err.getTraceback(),
                                           isdl.XenBEEClientError.SUBMISSION_FAILURE))
                )
            return None

        d.addCallback(handleSuccess)
        d.addErrback(_errFunc)

        self.transport.write(str(isdl.XenBEEClientError("image submitted: " + str(inst.getName()),
                                                        isdl.XenBEEClientError.OK)))

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
            signum = int(sig.firstChild.nodeValue.strip())
            if not signum in [ 9, 15 ]:
                raise ValueError("out of range, allowed are (9,15)")
        except Exception, e:
            self.transport.write(
                str(isdl.XenBEEClientError("Illegal signal: %s" % (e,),
                                           isdl.XenBEEClientError.ILLEGAL_REQUEST))
                )
            raise

        instN = isdl.getChild(node, "JobID")
        if not instN:
            self.transport.write(            
                str(isdl.XenBEEClientError("no instance given!",
                                           isdl.XenBEEClientError.ILLEGAL_REQUEST))
                )
            return
        instID = instN.firstChild.nodeValue.strip()
        inst = self.factory.instanceManager.lookupByUUID(instID)
        if not inst:
            self.transport.write(            
                str(isdl.XenBEEClientError("no such job: %s" % (instID,),
                                           isdl.XenBEEClientError.ILLEGAL_REQUEST))
                )
            return

        inst.stop()
        self.transport.write(str(isdl.XenBEEClientError("signal sent", isdl.XenBEEClientError.OK)))
	
class XenBEEInstanceProtocol(isdl.XMLProtocol):
    """The XBE instance side protocol.

    This protocol is spoken between an instance and the daemon.
    """

    def __init__(self, instid, transport):
        isdl.XMLProtocol.__init__(self, transport)
	self.instid = instid
        
    def do_InstanceAvailable(self, dom_node):
        inst_id = isdl.getChild(dom_node, "InstanceID").firstChild.nodeValue.strip()
        log.info("instance is available: %s" % inst_id)

class XenBEEProtocol(StompClient):
    """Processing input received by the STOMP server."""

    def __init__(self):
	self.factory = None
	StompClient.__init__(self)

    def connectedReceived(self, _):
	self.factory.stomp = self

	# i am connected to the stomp server
	log.debug("successfully connected to STOMP server, avaiting your commands.")
	self.subscribe(self.factory.queue, auto_ack=True)
	
    def messageReceived(self, msg):
        log.debug("got message: %s" % (str(msg),))
	if "client-id" in msg.header:
	    # request from some client
	    self.factory.newClient(msg, msg.header["client-id"])
	elif "instance-id" in msg.header:
	    # message from an instance
	    self.factory.newInstance(msg, msg.header["instance-id"])
	else:
	    log.warn("illegal message received")

    def errorOccured(self, msg, detail):
	log.error("error-message: '%s', details: '%s'" % (msg, detail))

class XenBEEProtocolFactory(StompClientFactory):
    protocol = XenBEEProtocol

    def __init__(self, scheduler, queue="/queue/xenbee/daemon"):
	StompClientFactory.__init__(self, user='daemon', password='none')
	self.queue = queue
	self.stomp = None
        self.scheduler = scheduler
	self.instanceManager = scheduler.instanceManager

    def clientConnectionFailed(self, connector, reason):
	log.error("connection to STOMP server failed!: %s" % reason)
	if 'twisted.internet.error.ConnectionRefusedError' in reason.parents:
            log.info("stopping the reactor...")
            reactor.stop()
	else:
	    StompClientFactory.clientConnectionFailed(self, connector, reason)

    def newClient(self, msg, client):
	clientProtocol = XenBEEClientProtocol(client,
                                              StompTransport(self.stomp,
                                                             "/queue/xenbee/client/"+str(client)))
	clientProtocol.factory = self
        reactor.callInThread(clientProtocol.messageReceived, msg)

    def newInstance(self, msg, instId):
        instProtocol = XenBEEInstanceProtocol(instId,
                                              StompTransport(self.stomp,
                                                             "/queue/xenbee/instance/"+str(instId)))
	instProtocol.factory = self
        reactor.callInThread(instProtocol.messageReceived, msg)

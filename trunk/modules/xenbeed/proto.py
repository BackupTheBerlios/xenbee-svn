#!/usr/bin/env python
"""
The Xen Based Execution Environment protocol
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

import logging
log = logging.getLogger(__name__)

from stomp.proto import StompClient, StompClientFactory
from xenbeed.instance import InstanceManager
from xenbeed import isdl

# Twisted imports
from twisted.internet import reactor

import xml.dom, threading
from xml.dom.ext.reader import PyExpat as XMLReaderBuilder

class StompTransport:
    """Simply wraps the message sending to write(text).

    Uses an existing STOMP Connection and a destination queue to send
    its data.
    """
    
    def __init__(self, stompConn, queue):
	"""Initialize the transport."""
	self.stomp = stompConn
	self.queue = queue
        self.mtx = threading.Lock()

    def write(self, data):
	"""Write data to the destination queue."""
        self.mtx.acquire()
	self.stomp.send(self.queue, data)
        self.mtx.release()
def ChildNodes(node, func=lambda n: n.nodeType == xml.dom.Node.ELEMENT_NODE):
    for c in filter(func, node.childNodes):
	yield c
class ElementNSFilter:
    def __init__(self, ns=isdl.ISDL_NS):
	self.ns = ns

    def __call__(self, n):
	return n.nodeType == xml.dom.Node.ELEMENT_NODE and n.namespaceURI == self.ns

class XenBEEClientProtocol:
    """The XBE client side protocol.

    This protocol is spoken between some client (user, script
    etc.). The protocol is based on XML
    """

    def __init__(self, client):
	self.xmlReader = XMLReaderBuilder.Reader()
	self.client = client
	self.dom = None
	self.transport = None

    def __del__(self):
	if self.dom:
	    self.xmlReader.releaseNode(self.dom)

    def messageReceived(self, msg):
	"""Handle a received message."""
	log.debug(msg)
	self.dom = self.xmlReader.fromString(msg.body)
	root = self.dom.documentElement
	# check the message
	if root.namespaceURI != isdl.ISDL_NS or root.localName != 'Message':
	    # got an unacceptable message
	    self.transport.write(str(isdl.XenBEEClientError("you sent me an illegal request!",
                                                            isdl.XenBEEClientError.ILLEGAL_REQUEST)))
	    return
	children = filter(ElementNSFilter(isdl.ISDL_NS), root.childNodes)
	if not len(children):
	    self.transport.write(str(isdl.XenBEEClientError("no elements from ISDL namespace found",
                                                            isdl.XenBEEClientError.ILLEGAL_REQUEST)))
	    return
	    
	try:
	    method = getattr(self, "do_" + children[0].localName)
	except AttributeError, ae:
	    self.transport.write(str(isdl.XenBEEClientError("you sent me an illegal request!",
                                                            isdl.XenBEEClientError.ILLEGAL_REQUEST)))
	    log.error("illegal request: " + str(ae))
	    return
	try:
	    method(children[0])
	except Exception, e:
	    self.transport.write(str(isdl.XenBEEClientError("submission failed: " + str(e),
                                                            isdl.XenBEEClientError.ILLEGAL_REQUEST)))
	    
    def __getChild(self, n, name, ns=isdl.ISDL_NS):
        try:
            return n.getElementsByTagNameNS(ns, name)[0]
        except:
            return None
	    
    def do_ImageSubmission(self, dom_node):
	"""Handle an image submission."""
	# parse image information and start retrieval of neccessary files
	imgDefNode = self.__getChild(dom_node, "ImageDefinition")
	if not imgDefNode:
	    raise Exception("no ImageDefinition found.")

	# boot block
	bootNode = self.__getChild(imgDefNode, "Boot")
	files = {}
	files["kernel"] = self.__getChild(
	    self.__getChild(bootNode, "Kernel"), "URI").firstChild.nodeValue.strip()
	files["initrd"] = self.__getChild(
	    self.__getChild(bootNode, "Initrd"), "URI").firstChild.nodeValue.strip()

	# image block
	imagesNode = self.__getChild(imgDefNode, "Images")

	bootImageNode = self.__getChild(imagesNode, "BootImage")
	files["root"] = self.__getChild(
	    self.__getChild(bootImageNode, "Source"), "URI").firstChild.nodeValue.strip()
	log.debug(files)

	# create instance and add files
	inst = self.factory.instanceManager.newInstance()
	d = inst.addFiles(files)

        def handleSuccess(_):
            self.transport.write(str(isdl.XenBEEClientError("image submitted: " + str(inst.getName()),
                                                            isdl.XenBEEClientError.OK)))
        d.addCallback(handleSuccess)
        
        def _errFunc(err):
            self.transport.write(            
                str(isdl.XenBEEClientError("file retrieval failed " + err.getTraceback(),
                                           isdl.XenBEEClientError.SUBMISSION_FAILURE))
                )
            return None
        d.addErrback(_errFunc)

    def do_StatusRequest(self, dom_node):
	"""Handle status request."""
        msg = isdl.XenBEEStatusMessage()
        map(msg.addStatusForInstance, self.factory.instanceManager)
        self.transport.write(str(msg))

    def do_Kill(self, node):
        # get the signal type
        sig = self.__getChild(node, "Signal")
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

        instN = self.__getChild(node, "JobID")
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

        def _s(_):
            self.factory.instanceManager.removeInstance(inst)
            self.transport.write(str(isdl.XenBEEClientError("job stopped", isdl.XenBEEClientError.OK)))
            
        inst.stop().addCallback(_s)
	
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
	if "client-id" in msg.header:
	    # request from some client
	    self.factory.newClient(msg, msg.header["client-id"])
	elif "instance-id" in msg.header:
	    # message from an instance
	    pass
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
	clientProtocol = XenBEEClientProtocol(client)
	clientProtocol.factory = self
	clientProtocol.transport = StompTransport(self.stomp, "/queue/xenbee/client/"+str(client))
	clientProtocol.messageReceived(msg)

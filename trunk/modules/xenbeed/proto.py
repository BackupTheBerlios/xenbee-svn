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

# Twisted imports
from twisted.internet import reactor

import xml.dom
from xml.dom.ext.reader import PyExpat as XMLReaderBuilder

ISDL_NS = u'http://www.example.com/schemas/isdl/2007/01/isdl'

class StompTransport:
    """Simply wraps the message sending to write(text).

    Uses an existing STOMP Connection and a destination queue to send
    its data.
    """
    
    def __init__(self, stompConn, queue):
	"""Initialize the transport."""
	self.stomp = stompConn
	self.queue = queue

    def write(self, data):
	"""Write data to the destination queue."""
	self.stomp.send(self.queue, data)

class XenBEEClientError:
    """Encapsulates errors using XML."""
    
    class OK:
	value = 200
	name = "OK"
    class ILLEGAL_REQUEST:
	value = 201
	name = "ILLEGAL REQUEST"
    class SUBMISSION_FAILURE:
	value = 202
	name = "SUBMISSION FAILURE"

    def __init__(self, msg, errcode):
	self.doc = xml.dom.getDOMImplementation().createDocument(ISDL_NS, "isdl:Message", None)

	root = self.doc.documentElement
	root.setAttributeNS(xml.dom.XMLNS_NAMESPACE, "xmlns:isdl", ISDL_NS)
	error = self.doc.createElementNS(ISDL_NS, "isdl:Error")
	errorCode = self.doc.createElementNS(ISDL_NS, "isdl:ErrorCode")
	errorCode.appendChild(self.doc.createTextNode(str(errcode.value)))
	errorName = self.doc.createElementNS(ISDL_NS, "isdl:ErrorName")
	errorName.appendChild(self.doc.createTextNode(errcode.name))
	errorMessage = self.doc.createElementNS(ISDL_NS, "isdl:ErrorMessage")
	errorMessage.appendChild(self.doc.createTextNode(msg))
	
	error.appendChild(errorCode)
	error.appendChild(errorName)
	error.appendChild(errorMessage)
	root.appendChild(error)
	self.doc.normalize()
	
    def __str__(self):
	return self.doc.toprettyxml(indent='  ', encoding='UTF-8')

def ChildNodes(node, func=lambda n: n.nodeType == xml.dom.Node.ELEMENT_NODE):
    for c in filter(func, node.childNodes):
	yield c
class ElementNSFilter:
    def __init__(self, ns=ISDL_NS):
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
	
	self.dom = self.xmlReader.fromString(msg.body)
	root = self.dom.documentElement
	# check the message
	if root.namespaceURI != ISDL_NS or root.nodeName != u'isdl:Message':
	    # got an unacceptable message
	    self.transport.write(str(XenBEEClientError("you sent me an illegal request!",
						       XenBEEClientError.ILLEGAL_REQUEST)))
	    return
	children = filter(ElementNSFilter(ISDL_NS), root.childNodes)
	if not len(children):
	    self.transport.write(str(XenBEEClientError("no elements from ISDL namespace found",
						       XenBEEClientError.ILLEGAL_REQUEST)))
	    return
	    
	try:
	    method = getattr(self, "do_" + children[0].localName)
	except AttributeError, ae:
	    self.transport.write(str(XenBEEClientError("you sent me an illegal request!",
						       XenBEEClientError.ILLEGAL_REQUEST)))
	    log.error("illegal request: " + str(ae))
	    return
	try:
	    method(children[0])
	except Exception, e:
	    self.transport.write(str(XenBEEClientError("submission failed: " + str(e),
						       XenBEEClientError.ILLEGAL_REQUEST)))
	    
    def do_ImageSubmission(self, dom_node):
	"""Handle an image submission."""
	def getChild(n, name, ns=ISDL_NS):
	    try:
		return n.getElementsByTagNameNS(ISDL_NS, name)[0]
	    except:
		return None
	    
	# parse image information and start retrieval of neccessary files
	imgDefNode = getChild(dom_node, "ImageDefinition")
	if not imgDefNode:
	    raise Exception("no ImageDefinition found.")

	# boot block
	bootNode = getChild(imgDefNode, "Boot")
	files = {}
	files["kernel"] = getChild(
	    getChild(bootNode, "Kernel"), "URI").firstChild.nodeValue.strip()
	files["initrd"] = getChild(
	    getChild(bootNode, "Initrd"), "URI").firstChild.nodeValue.strip()

	# image block
	imagesNode = getChild(imgDefNode, "Images")

	bootImageNode = getChild(imagesNode, "BootImage")
	files["image"] = getChild(
	    getChild(bootImageNode, "Source"), "URI").firstChild.nodeValue.strip()
	log.debug(files)

	# create instance and add files
	inst = self.factory.instanceManager.newInstance()
	inst.addFiles(files)
	self.transport.write(str(XenBEEClientError("executing image : " + str(files),
						   XenBEEClientError.OK)))

    def do_StatusRequest(self, dom_node):
	"""Handle status request."""
	
	
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
	log.debug("got message\n%s" % msg.body)
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

    def __init__(self, queue="/queue/xenbee/daemon"):
	StompClientFactory.__init__(self, user='daemon', password='none')
	self.queue = queue
	self.stomp = None
	self.instanceManager = InstanceManager()

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

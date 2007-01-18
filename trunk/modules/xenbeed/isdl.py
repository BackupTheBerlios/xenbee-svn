#!/usr/bin/env python
"""
The Xen Based Execution Environment XML Messages
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging
log = logging.getLogger(__name__)

import xml.dom
from xml.dom.ext.reader import PyExpat as XMLReaderBuilder

ISDL_NS = u'http://www.example.com/schemas/isdl/2007/01/isdl'
def ChildNodes(node, func=lambda n: n.nodeType == xml.dom.Node.ELEMENT_NODE):
    for c in filter(func, node.childNodes):
	yield c

class ElementFilter:
    def __init__(self, other_filter=None, op=lambda x,y: x and y):
        self.op = op
        self.other = other_filter or (lambda x: True)

    def __call__(self, node):
        return self.op(self.other(node), node.nodeType == xml.dom.Node.ELEMENT_NODE)
    
class ElementNSFilter(ElementFilter):
    def __init__(self, ns=ISDL_NS):
	self.ns = ns

    def __call__(self, n):
	return n.nodeType == xml.dom.Node.ELEMENT_NODE and n.namespaceURI == self.ns

class XMLProtocol(object):
    """The base class of all here used client-protocols."""

    def __init__(self, transport):
        self.xmlReader = XMLReaderBuilder.Reader()
        self.dom = None
        self.transport = transport
        self.factory = None

    def __del__(self):
	if self.dom:
	    self.xmlReader.releaseNode(self.dom)

    def dispatch(self, func, *args, **kw):
	try:
	    method = getattr(self, "do_" + func)
	except AttributeError, ae:
	    self.transport.write(str(XenBEEClientError("you sent me an illegal request!",
                                                            XenBEEClientError.ILLEGAL_REQUEST)))
	    log.error("illegal request: " + str(ae))
            raise
	try:
	    method(*args, **kw)
	except Exception, e:
	    self.transport.write(str(XenBEEClientError("request failed: " + str(e),
                                                            XenBEEClientError.ILLEGAL_REQUEST)))
            raise
        
    def messageReceived(self, msg):
        try:
            return self._messageReceived(msg)
        except:
            log.exception("message handling failed")

    def _messageReceived(self, msg):
	"""Handle a received message."""
	self.dom = self.xmlReader.fromString(msg.body)
	root = self.dom.documentElement
	# check the message
	if root.namespaceURI != ISDL_NS or root.localName != 'Message':
	    # got an unacceptable message
	    self.transport.write(str(isdl.XenBEEClientError("you sent me an illegal request!",
                                                            XenBEEClientError.ILLEGAL_REQUEST)))
	    return
	children = filter(ElementFilter(), root.childNodes)
	if not len(children):
	    self.transport.write(str(XenBEEClientError("no elements from ISDL namespace found",
                                                       XenBEEClientError.ILLEGAL_REQUEST)))
	    return
        map(log.debug, map(str, children))
        self.dispatch(children[0].localName, children[0])
        
def getChild(node, name, ns=ISDL_NS):
    try:
        return node.getElementsByTagNameNS(ns, name)[0]
    except:
        return None
	    

class XenBEEMessageFactory:
    namespace = ISDL_NS
    
    def __init__(self, prefix="isdl"):
        self.prefix = prefix

class XenBEEClientMessage:
    """Encapsulates a xml message."""
    def __init__(self, namespace=ISDL_NS, prefix="isdl"):
        self.ns = namespace
        self.prefix = prefix
        self.initXML()

    def initXML(self):
	self.doc = xml.dom.getDOMImplementation().createDocument(self.ns,
                                                                 self.prefix+":"+"Message",
                                                                 None)
	self.root = self.doc.documentElement
        self.root.setAttributeNS(xml.dom.XMLNS_NAMESPACE, "xmlns:"+self.prefix, self.ns)
        

    def createElement(self, name, parent=None, text=None):
        if not self.doc:
            raise RuntimeError("initXML() has to be called first")
        e = self.doc.createElementNS(self.ns, self.prefix + ":" + name)
        if text:
            e.appendChild(self.doc.createTextNode(str(text)))
        if parent:
            parent.appendChild(e)
        return e

    def __str__(self):
        if self.doc:
            return self.doc.toprettyxml(indent='  ', encoding='UTF-8')
        else:
            raise RuntimeError("message contains no document")

class XenBEEClientError(XenBEEClientMessage):
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
        XenBEEClientMessage.__init__(self)
        self.msg = msg
        self.errcode = errcode
        self.toxml()

    def toxml(self):
	error = self.createElement("Error", self.root)
	errorCode = self.createElement("ErrorCode", error, self.errcode.value)
	errorName = self.createElement("ErrorName", error, self.errcode.name)
	errorMessage = self.createElement("ErrorMessage", error, self.msg)
        return self.__str__()

class XenBEEStatusMessage(XenBEEClientMessage):
    """Encapsulates the status of all known tasks.

    <StatusList>
        <Status>
           <Name></Name>
           <User></User>
           <Memory></Memory>
           <CPUTime></CPUTime>
           <StartTime></StartTime>
           <EndTime></EndTime>
           <State></State>
        </Status>
        <Status>

        </Status>
    </StatusList>

    """

    def __init__(self):
        XenBEEClientMessage.__init__(self)
        self.statusList = self.createElement("StatusList", self.root)

    def addStatusForInstance(self, obj):
        status = self.createElement("Status", self.statusList)
        if obj.state == "started":
            objInfo = obj.getBackendInfo()
        else:
            objInfo = None
        
        def _c(name, txt=None):
            self.createElement(name, status, txt)
        _c("Name", obj.getName())
        _c("User", "N/A")
        if objInfo:
            _c("Memory", objInfo.memory)
            _c("CPUTime", objInfo.cpuTime)
        else:
            _c("Memory", "N/A")
            _c("CPUTime", "N/A")
            
        _c("StartTime", obj.startTime)
        _c("EndTime", "N/A")
        _c("State", obj.state)

class XenBEEInstanceAvailable(XenBEEClientMessage):
    """The message sent by an instance upon startup."""

    def __init__(self, inst_id):
        XenBEEClientMessage.__init__(self)
        self.instanceId = inst_id
        ia = self.createElement("InstanceAvailable", self.root)
        self.createElement("InstanceID", ia, str(self.instanceId))


#!/usr/bin/env python
"""
The Xen Based Execution Environment XML Messages
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging
log = logging.getLogger(__name__)

import xml.dom.minidom
from xml.dom.ext import PrettyPrint

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

ISDL_NS = u'http://www.example.com/schemas/isdl/2007/01/isdl'
JSDL_NS = u'http://schemas.ggf.org/jsdl/2005/11/jsdl'
JSDL_POSIX_NS = u'http://schemas.ggf.org/jsdl/2005/11/jsdl-posix'


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
        self.__dom = None
        self.transport = transport
        self.factory = None

        # a list of (localName, namespaceURI) tuples that are
        # understood by the protocol
        self.__understood = []
        self.addUnderstood("Error", ISDL_NS)

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

    def addUnderstood(self, localname, ns_uri):
        pair = (localname, ns_uri)
        if pair not in self.__understood:
            self.__understood.append(pair)

    def messageReceived(self, msg):
        try:
            return self._messageReceived(msg)
        except Exception, e:
            log.exception("message handling failed")
            self.transport.write(str(XenBEEClientError("handling failed: %s" % (str(e),),
                                                       XenBEEClientError.ILLEGAL_REQUEST)))

    def _messageReceived(self, msg):
	"""Handle a received message."""
	self.__dom = xml.dom.minidom.parseString(msg.body)
        self.__dom.normalize()
	root = self.__dom.documentElement
	# check the message
	if root.namespaceURI != ISDL_NS or root.localName != 'Message':
	    # got an unacceptable message
	    self.transport.write(str(XenBEEClientError("you sent me an illegal message!",
                                                            XenBEEClientError.ILLEGAL_REQUEST)))
	    return
	children = filter(ElementFilter(), root.childNodes)
	if not len(children):
	    self.transport.write(str(XenBEEClientError("no elements to handle found, sorry",
                                                       XenBEEClientError.ILLEGAL_REQUEST)))
	    return
        map(log.debug, map(NodeToString, children))

        for c in children:
            if (c.localName, c.namespaceURI) in self.__understood:
                self.dispatch(c.localName, c)

    def do_Error(self, err_node):
        log.debug("got error:\n%s" % (NodeToString(err_node)))

#######
# The following code has been taken from:
#
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/135131

def in_order_iterator_filter(node, filter_func):
    if filter_func(node):
        yield node
    for child in node.childNodes:
        for cn in in_order_iterator_filter(child, filter_func):
            if filter_func(cn):
                yield cn
    return

def get_elements_by_tag_name_ns(node, ns, local):
    return in_order_iterator_filter(
        node,
        lambda n: n.nodeType == xml.dom.Node.ELEMENT_NODE and \
                  n.namespaceURI == ns and n.localName == local
        )

def string_value(node):
    text_nodes = in_order_iterator_filter(
        node, lambda n: n.nodeType == xml.dom.Node.TEXT_NODE)
    return u''.join([ n.data for n in text_nodes ])

#######

def getChild(node, name, ns=ISDL_NS):
    try:
        return node.getElementsByTagNameNS(ns, name)[0]
    except:
        return None

def NodeToString(node):
    node.normalize()
    buf = StringIO()
    PrettyPrint(node, indent='  ', stream=buf)
    buf.flush()
    buf.seek(0,0)
    return buf.getvalue()
        
class XenBEEMessageFactory:
    namespace = ISDL_NS
    
    def __init__(self, prefix="isdl"):
        self.prefix = prefix

class XenBEEClientMessage:
    """Encapsulates a xml message."""
    def __init__(self, namespace=ISDL_NS, prefix="isdl"):
        self.__ns = namespace
        self.__prefix = prefix
        self.__doc = None
        self.root = None
        self.__initXML()

    def __initXML(self):
	self.__doc = xml.dom.minidom.getDOMImplementation().createDocument(self.__ns,
                                                                           self.__prefix+":"+"Message",
                                                                           None)
	self.root = self.__doc.documentElement
        self.addNamespace(self.__prefix, self.__ns)

    def addNamespace(self, prefix, uri):
        self.root.setAttributeNS(xml.dom.XMLNS_NAMESPACE, "xmlns:"+prefix, uri)
        return self

    def createElement(self, name, parent=None, text=None):
        if not self.__doc:
            raise RuntimeError("initXML() has to be called first")
        e = self.__doc.createElementNS(self.__ns, self.__prefix + ":" + name)
        if text:
            e.appendChild(self.__doc.createTextNode(str(text)))
        if parent:
            parent.appendChild(e)
        return e

    def __str__(self):
        if self.__doc:
            return NodeToString(self.__doc)
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

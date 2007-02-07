#!/usr/bin/env python
"""
The Xen Based Execution Environment XML Messages
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging
log = logging.getLogger(__name__)

from time import gmtime, strftime
from lxml import etree
import re

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

ISDL_NS = "http://www.example.com/schemas/isdl/2007/01/isdl"
JSDL_NS = "http://schemas.ggf.org/jsdl/2005/11/jsdl"
JSDL_POSIX_NS = "http://schemas.ggf.org/jsdl/2005/11/jsdl-posix"


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
        self.transport = transport
        self.factory = None

        # a list of ({uri}localName) tuples that are
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

    def addUnderstood(self, elementName, namespace):
        tag = Tag(elementName, namespace)
        if tag not in self.__understood:
            self.__understood.append(tag)

    def messageReceived(self, msg):
        try:
            return self._messageReceived(msg)
        except Exception, e:
            log.exception("message handling failed")
            self.transport.write(str(XenBEEClientError("handling failed: %s" % (str(e),),
                                                       XenBEEClientError.ILLEGAL_REQUEST)))

    def _messageReceived(self, msg):
	"""Handle a received message."""
	self.__root = etree.fromstring(msg.body)
        
	# check the message
	if self.__root.tag != (Tag("Message", ISDL_NS)):
	    # got an unacceptable message
	    self.transport.write(str(XenBEEClientError("you sent me an illegal message!",
                                                       XenBEEClientError.ILLEGAL_REQUEST)))
	    return

	if not len(self.__root):
	    self.transport.write(str(XenBEEClientError("no elements to handle found, sorry",
                                                       XenBEEClientError.ILLEGAL_REQUEST)))
	    return
        for child in filter(lambda x: x.tag in self.__understood, self.__root):
            self.dispatch(decodeTag(child.tag)[1], child)

    def do_Error(self, err):
        log.debug("got error:\n%s" % (etree.tostring(err)))

__tagPattern = re.compile(r"^(?P<nsuri>{.*})?(?P<local>.*)$")

def decodeTag(tag):
    m = __tagPattern.match(tag)
    return (m.group("nsuri"), m.group("local"))

def Tag(local, uri=ISDL_NS):
    return etree.QName(uri, local).text

def getChild(elem, name, ns=ISDL_NS):
    return elem.find(Tag(name,ns))

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
        """Initialize a XML message using the given namespace and prefix."""
        self.__ns = namespace
        self.__prefix = prefix
        self.root = etree.Element(Tag("Message", self.__ns), nsmap={ prefix: namespace } )

    def createElement(self, tag, parent=None, text=None):
        """Utility function to create a new element for this message."""
        if parent == None: parent = self.root
        e = etree.SubElement(parent, Tag(tag, self.__ns))
        if text != None:
            e.text = str(text)
        return e

    def __str__(self):
        return etree.tostring(self.root)

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
#        error["code"] = str(self.errcode.value)
#        error["name"] = str(self.errcode.name)
	errorCode = self.createElement("ErrorCode", error, str(self.errcode.value))
	errorName = self.createElement("ErrorName", error, self.errcode.name)
	errorMessage = self.createElement("ErrorMessage", error, self.msg)

class XenBEEStatusMessage(XenBEEClientMessage):
    """Encapsulates the status of all known tasks.

    <StatusList>
        <Status>
           <ID></ID>
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

    def addStatusForTask(self, task):
        status = self.createElement("Status", self.statusList)

        try:
            info = task.inst.getBackendInfo()
        except:
            info = None
        
        def _c(name, txt):
            self.createElement(name, status, str(txt))
        _c("ID", task.ID())
        _c("User", "N/A")
        _c("Submitted", str(task.tstamp))
        if info:
            _c("Memory", info.memory)
            _c("CPUTime", info.cpuTime)
        else:
            _c("Memory", "N/A")
            _c("CPUTime", "N/A")
        if hasattr(task, "startTime"):
            _c("StartTime", str(task.startTime))
        else:
            _c("StartTime", "N/A")
        if hasattr(task, "endTime"):
            _c("EndTime", str(task.endTime))
        else:
            _c("EndTime", "N/A")
        _c("State", task.state())
        if hasattr(task, "exitCode"):
            _c("ExitCode", str(task.exitCode))
        else:
            _c("ExitCode", "N/A")
            

class XenBEEInstanceAvailable(XenBEEClientMessage):
    """The message sent by an instance upon startup."""

    def __init__(self, inst_id):
        XenBEEClientMessage.__init__(self)
        self.instanceId = inst_id
        ia = self.createElement("InstanceAvailable", self.root)
        self.createElement("InstanceID", ia, str(self.instanceId))

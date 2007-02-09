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
from twisted.internet import defer, threads
import re

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

XSDL_NS = "http://www.example.com/schemas/xsdl/2007/01/xsdl"
JSDL_NS = "http://schemas.ggf.org/jsdl/2005/11/jsdl"
JSDL_POSIX_NS = "http://schemas.ggf.org/jsdl/2005/11/jsdl-posix"

def decodeTag(tag):
    m = __tagPattern.match(tag)
    return (m.group("nsuri"), m.group("local"))

def Tag(local, ns=XSDL_NS):
    return "{%s}%s" % (ns, local)

# taken from http://effbot.org/zone/element-lib.htm
class NS(object):
    def __init__(self, uri):
        self.__uri = uri
    def __getattr__(self, tag):
        return Tag(tag, self.__uri)
    def __call__(self, path):
        return "/".join([getattr(self, tag) for tag in path.split("/")])

XSDL = NS(XSDL_NS)
JSDL = NS(JSDL_NS)
JSDL_POSIX = NS(JSDL_POSIX_NS)

class XMLProtocol(object):
    """The base class of all here used client-protocols."""

    def __init__(self, transport):
        self.transport = transport
        self.factory = None

        # a list of ({uri}localName) tuples that are
        # understood by the protocol
        self.__understood = []
        self.addUnderstood(Tag("Error"))

    def dispatch(self, func, *args, **kw):
	try:
	    method = getattr(self, "do_" + func)
	except AttributeError, ae:
	    self.transport.write(str(XenBEEClientError("you sent me an illegal request!",
                                                       XenBEEClientError.ILLEGAL_REQUEST)))
	    log.error("illegal request: " + str(ae))
            return defer.fail(ae)
	try:
	    return threads.deferToThread(method, *args, **kw)
	except Exception, e:
	    self.transport.write(str(XenBEEClientError("request failed: " + str(e),
                                                       XenBEEClientError.INTERNAL_SERVER_ERROR)))
            return defer.fail(e)

    def addUnderstood(self, tag):
        if tag not in self.__understood:
            self.__understood.append(tag)

    def messageReceived(self, msg):
        def _f(err):
            errmsg = "message handling failed: %s\n%s" % (err.getErrorMessage(), err.getTraceback())
            log.warn(errmsg)
            self.transport.write(str(XenBEEClientError(errmsg)))
            return msg
        try:
            return self._messageReceived(msg).addErrback(_f)
        except Exception, e:
            log.exception("message handling failed")
            self.transport.write(str(XenBEEClientError("handling failed: %s" % (str(e),),
                                                       XenBEEClientError.ILLEGAL_REQUEST)))

    def _messageReceived(self, msg):
	"""Handle a received message."""
	self.__root = etree.fromstring(msg.body)
        
	# check the message
        if self.__root.tag != Tag("Message"):
	    # got an unacceptable message
#	    self.transport.write(str(XenBEEClientError("you sent me an illegal message!",
#                                                       XenBEEClientError.ILLEGAL_REQUEST)))
	    return defer.fail(RuntimeError("you sent me an illegal message!"))

	if not len(self.__root):
#	    self.transport.write(str(XenBEEClientError("no elements to handle found, sorry",
#                                                       XenBEEClientError.ILLEGAL_REQUEST)))
	    return defer.fail("no elements to handle found, sorry")
        
        for child in filter(lambda x: x.tag in self.__understood, self.__root):
            return self.dispatch(decodeTag(child.tag)[1], child)
        return defer.fail(ValueError("no acceptable tag found"))
    
    def do_Error(self, err):
        log.debug("got error:\n%s" % (etree.tostring(err)))

__tagPattern = re.compile(r"^(?P<nsuri>{.*})?(?P<local>.*)$")

def getChild(elem, name, ns=XSDL):
    return elem.find(ns(name))

def NodeToString(node):
    node.normalize()
    buf = StringIO()
    PrettyPrint(node, indent='  ', stream=buf)
    buf.flush()
    buf.seek(0,0)
    return buf.getvalue()
        
class XenBEEMessageFactory:
    namespace = XSDL_NS
    
    def __init__(self, prefix="xsdl"):
        self.prefix = prefix

class XenBEEClientMessage:
    """Encapsulates a xml message."""
    def __init__(self, namespace=XSDL_NS, prefix="xsdl"):
        """Initialize a XML message using the given namespace and prefix."""
        self.__ns = namespace
        self.__prefix = prefix
        self.root = etree.Element(Tag("Message", namespace), nsmap={ prefix: namespace } )

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
    class INTERNAL_SERVER_ERROR:
        value = 500
        name = "INTERNAL_SERVER_ERROR"

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

class XenBEEListCache(XenBEEClientMessage):
    """Request to list the cache entries."""

    def __init__(self):
        XenBEEClientMessage.__init__(self)
        self.__request = self.createElement("ListCache", self.root)

class XenBEECacheEntries(XenBEEClientMessage):
    """Message sent to a client when a list of the cache is requested."""

    def __init__(self):
        XenBEEClientMessage.__init__(self)
        self.__entries = self.createElement("CacheEntries", self.root)

    def addEntry(self, uuid, type, description):
        e = self.createElement("Entry", self.__entries)
        self.createElement("URI", e, "cache://xbe-file-cache/"+str(uuid))
        self.createElement("Type", e, str(type))
        self.createElement("Description", e, str(description))

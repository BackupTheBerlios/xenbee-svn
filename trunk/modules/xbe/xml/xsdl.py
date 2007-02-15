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
from twisted.python import failure
import re

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

from xbe.xml.namespaces import *

class XMLProtocol(object):
    """The base class of all here used client-protocols."""

    def __init__(self, transport):
        self.transport = transport
        self.factory = None

        # a list of ({uri}localName) tuples that are
        # understood by the protocol
        self.__understood = []
        self.addUnderstood(XSDL("Error"))

    def dispatch(self, elem, *args, **kw):
        method = getattr(self, "do_%s" % (decodeTag(elem.tag)[1]))
        return method(elem, *args, **kw)

    def addUnderstood(self, tag):
        if tag not in self.__understood:
            self.__understood.append(tag)

    def transformResultToMessage(self, result):
        if isinstance(result, failure.Failure):
            result = XenBEEError(result.getErrorMessage(),
                                 ErrorCode.INTERNAL_SERVER_ERROR)
        if result is None:
            # do not reply, so return None
            return None
        if not isinstance(result, XenBEEMessage):
            result = XenBEEError(repr(result),
                                 ErrorCode.INTERNAL_SERVER_ERROR)

        # result is now a XenBEEMessage
        return result

    def sendMessage(self, msg):
        if msg is None:
            log.debug("nothing to answer...")
        else:
            assert isinstance(msg, XenBEEMessage)
            self.transport.write(msg.to_xml())
        return msg

    def messageReceived(self, msg):
        """Handle an incoming XML message.

        The message handling code works as follows:

             * a method is looked up according to the 'tag' of the root element
               or the first direct child that 
        """
        d = defer.maybeDeferred(self._messageReceived, msg)
        d.addBoth(self.transformResultToMessage)
        d.addCallback(self.sendMessage)
        return d

    def _messageReceived(self, msg):
	"""Handle a received message."""
        return self.dispatch(etree.fromstring(msg.body))

    # some default xml-element handler
    #
    def do_Message(self, msg):
        # handle a XBE-Message
        #
        # try to split the message up into header and body
        #
        # else handle just the first element
        header = msg.find(XBE("MessageHeader"))
        if header is not None:
            log.debug("got new style message")
        else:
            return self.dispatch(msg[0])
        
    def do_Error(self, err):
        log.debug("got error:\n%s" % (etree.tostring(err)))

class XenBEEMessage(object):
    """Encapsulates a xml message."""
    def __init__(self, namespace=XSDL_NS, prefix="xsdl"):
        """Initialize a XML message using the given namespace and prefix."""
        self.__ns = NS(namespace)
        self.__prefix = prefix
        self.root = etree.Element(self.__ns("Message"), nsmap={ prefix: namespace})

    def createElement(self, tag, parent=None, text=None):
        """Utility function to create a new element for this message."""
        if parent == None: parent = self.root
        e = etree.SubElement(parent, self.__ns(tag))
        if text != None:
            e.text = str(text)
        return e

    def __str__(self):
        return etree.tostring(self.root)

    def to_s(self):
        return str(self)
    def to_xml(self):
        return self.to_s()

class ErrorCode:
    class OK:
	value = 200
	name = "OK"
        short_msg = "everything ok"
        long_msg  = short_msg
    class ILLEGAL_REQUEST:
	value = 400
	name = "ILLEGAL REQUEST"
        short_msg = "you sent me an illegal request"
        long_msg  = short_msg
    class SUBMISSION_FAILURE:
	value = 401
	name = "SUBMISSION FAILURE"
        short_msg = "you sent me an illegal request"
        long_msg  = short_msg
    class TASK_LOOKUP_FAILURE:
        value = 404
        name = "TASK_LOOKUP_FAILURE"
        short_msg = "the task-id you sent could not be mapped to a task"
        long_msg  = short_msg
    class INSTANCE_LOOKUP_FAILURE:
        value = 405
        name = "INSTANCE_LOOKUP_FAILURE"
        short_msg = "the task-id you sent could not be mapped to a task"
        long_msg  = short_msg

    class SIGNAL_OUT_OF_RANGE:
        value = 450
        name = "SIGNAL_OUT_OF_RANGE"
        short_msg = "the signal you have sent was out of range"
        long_msg  = short_msg


    class INTERNAL_SERVER_ERROR:
        value = 500
        name = "INTERNAL_SERVER_ERROR"
        short_msg = "you sent me an illegal request"
        long_msg  = short_msg
    
    
class XenBEEError(XenBEEMessage):
    """Encapsulates errors using XML."""
    
    def __init__(self, msg, errcode):
        XenBEEMessage.__init__(self)
        self.msg = msg
        self.errcode = errcode

	error = self.createElement("Error", self.root)
        error.attrib[XSDL("code")] = str(self.errcode.value)
	errorCode = self.createElement("ErrorCode", error, str(self.errcode.value))
	errorName = self.createElement("ErrorName", error, self.errcode.name)
	errorMessage = self.createElement("ErrorMessage", error, self.msg)

class XenBEEClientMessage(XenBEEMessage):
    pass

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
            info = task.inst.getInfo()
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
            if len(info.ips):
                _c("IP", info.ips[0])
            else:
                _c("IP", 'n/a')
            _c("FQDN", info.fqdn)
        else:
            _c("Memory", "N/A")
            _c("CPUTime", "N/A")
            _c("IP", 'n/a')
            _c("FQDN", 'n/a')
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
        self.nodeInfo = self.createElement("NodeInformation", ia)

    def setNetworkInfo(self, fqdn, ips):
        netinfo = self.createElement("Network", self.nodeInfo)
        self.createElement("FQDN", netinfo, fqdn)
        ipinfo = self.createElement("IPList", netinfo)
        for ip in ips:
            self.createElement("IP", ipinfo, ip)

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

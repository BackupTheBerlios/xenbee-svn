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

class XenBEEClientMessage:
    """Encapsulates a xml message."""
    def __init__(self, namespace=ISDL_NS, prefix="isdl"):
        self.ns = namespace
        self.prefix = prefix
	self.doc = xml.dom.getDOMImplementation().createDocument(self.ns, self.prefix+":"+"Message", None)
	self.root = self.doc.documentElement
        self.root.setAttributeNS(xml.dom.XMLNS_NAMESPACE, "xmlns:"+self.prefix, self.ns)

    def createElement(self, name, parent=None, text=None):
        e = self.doc.createElementNS(self.ns, self.prefix + ":" + name)
        if text:
            e.appendChild(self.doc.createTextNode(str(text)))
        if parent:
            parent.appendChild(e)
        return e

    def __str__(self):
	return self.doc.toprettyxml(indent='  ', encoding='UTF-8')

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
	error = self.createElement("Error", self.root)
	errorCode = self.createElement("ErrorCode", error, errcode.value)
	errorName = self.createElement("ErrorName", error, errcode.name)
	errorMessage = self.createElement("ErrorMessage", error, msg)

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
        objInfo = obj.getBackendInfo()
        
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

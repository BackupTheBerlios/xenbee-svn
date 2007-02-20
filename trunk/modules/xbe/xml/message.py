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
from xbe.xml import errcode

class MessageParserError(ValueError):
    pass

class MessageBuilder(object):
    """Transforms xml documents back to its Message instance."""
    builder_map = {}

    def register(cls, klass):
        """Register a new Message class.

        klass.tag is used to identify the matching body element:
        Example:
           suppose the following message:
           
           <Message>
              <MessageHeader/>
              <MessageBody><Foo/>
           </Message>

           A class registering with 'Foo' will be used to transform
           'Foo' back to a Foo-instance.
           
        """
        MessageBuilder.builder_map[klass.tag] = klass
    register = classmethod(register)

    def lookup(cls, tag):
        return MessageBuilder.builder_map[tag]
    lookup = classmethod(lookup)

    def xml_parts(cls, xml_document=None):
        """return a tuple consisting of (roottree, header, body)"""
        if xml_document is None:
            root = etree.Element(XBE("Message"), nsmap={"xbe": str(XBE)})
            hdr  = etree.SubElement(root, XBE("MessageHeader"))
            body = etree.SubElement(root, XBE("MessageBody"))
        else:
            root = xml_document
            hdr = xml_document.find(XBE("MessageHeader"))
            body = xml_document.find(XBE("MessageBody"))
        return root, hdr, body
    xml_parts = classmethod(xml_parts)

    def from_xml(cls, xml_document):
        """A factory method, that can be used to transform a xml
        document the matching Message instance.

        @param xml_document a etree.Element or etree.ElementTree
        @return the matching Message instance or a failure.Failure instance
        """
        root, hdr, body = MessageBuilder.xml_parts(xml_document)
        if not body or not len(body):
            tag = None
        else:
            tag = body[0].tag
        builder = MessageBuilder.lookup(tag)
        if builder is not None:
            try:
                result = builder.from_xml(root, hdr, body)
            except Exception, e:
                raise
            return result
        else:
            return failure.Failure(LookupError("could not find builder for tag '%s'" % (tag,)))
    from_xml = classmethod(from_xml)


class Message(object):
    def __init__(self):
        pass
    
    def as_xml(self):
        return MessageBuilder.xml_parts()[0]
    
    def as_str(self):
        return str(self)

    def __str__(self):
        return etree.tostring(self.as_xml())

class SimpleMessage(Message):
    pass

class Error(SimpleMessage):
    ns  = XBE
    tag = ns("Error")
    
    def __init__(self, code=errcode.OK, msg=None):
        self.info = errcode.info[code]
        self.code = code
        self.message = msg

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
	error = etree.SubElement(body, self.tag)
        
        error.attrib[Error.ns("code")] = str(self.code)
	etree.SubElement(error, self.ns("ErrorName")).text = self.info[0]
        etree.SubElement(error, self.ns("ErrorDescription")).text = self.info[1]
        if self.message is not None:
            etree.SubElement(error, self.ns("ErrorMessage")).text = self.message
        return root

    def from_xml(cls, root, hdr, body):
        error = body.find(self.tag)
        code = int(error.attrib[cls.ns("code")])
        msg = error.findtext(cls.ns("ErrorMessage"))
        return cls(code, msg)
    from_xml = classmethod(from_xml)
MessageBuilder.register(Error)        

#############################
#
# security related messages
#
#############################
class CertificateRequest(SimpleMessage):
    """Represents the request for a certificate.

    currently an empty message, that does only contain an
    CertificateRequest body element.
    """
    tag = XBE("CertificateRequest")
    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        etree.SubElement(body, self.tag)
        return root

    def from_xml(cls, root, hdr, body):
        return cls()
    from_xml = classmethod(from_xml)
MessageBuilder.register(CertificateRequest)

class Certificate(Message):
    """Represents a certificate.

    it only contains a header, that holds a signed X509 certificate.
    see xml.security.X509SecurityLayer for information about signing.
    """
    def __init__(self, securityLayer):
        Message.__init__(self)
        self.__securityLayer = securityLayer

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        # sign the message
        root, signature = self.__securityLayer.sign(root, include_certificate=True)
        return root

#############################
#
#   client/server messages
#
#############################

class BaseClientMessage(SimpleMessage):
    pass

class BaseServerMessage(SimpleMessage):
    pass

#
# cache access
#
class ListCache(BaseClientMessage):
    """Request a list of all cached files.

    only body element is "ListCache"
    """
    tag = XBE("ListCache")
    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        etree.SubElement(body, self.tag)
        return root
    def from_xml(cls, root, hdr, body):
        return cls()
    from_xml = classmethod(from_xml)
MessageBuilder.register(ListCache)

class CacheEntries(BaseServerMessage):
    """Answers the ListCache request.

    Holds a list of cache entries.
    """
    tag = XBE("CacheEntries")
    
    def __init__(self):
        BaseServerMessage.__init__(self)
        self.__entries = []

    def add(self, uri, hash, type="data", description=""):
        self.__entries.append({"URI": uri,
                               "HashValue": hash,
                               "Type": type,
                               "Description": description})

    def entries(self):
        return self.__entries

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        entries = etree.SubElement(body, self.tag)
        for entry in self.__entries:
            e = etree.SubElement(entries, XBE("Entry"))
            for key, value in entry.iteritems():
                etree.SubElement(e, XBE(key)).text = str(value)
        return root
    
    def from_xml(cls, root, hdr, body):
        cache_entries = cls()
        entries = body.find(cls.tag)
        for entry in entries:
            entry_info = {}
            for info_elem in entry:
                key = decodeTag(info_elem.tag)[1]
                value = info_elem.text
                entry_info[key] = value
            cache_entries.__entries.append(entry_info)
        return cache_entries
    from_xml = classmethod(from_xml)
MessageBuilder.register(CacheEntries)

#
# job control
#

class Kill(BaseClientMessage):
    """Sends a signal to the given task.

    possible signal values are:
          0 - just check the task_id (whatever that may be good for)
          9 - definitively kill the task
         15 - send a termination request

    <Kill signal="sig"><Task>task_id</Task></Kill>
    """
    tag = XBE("Kill")
    
    def __init__(self, task_id=None, signal=15):
        BaseClientMessage.__init__(self)
        self.__task_id = task_id
        self.__signal = signal

    def signal(self):
        return self.__signal
    def task_id(self):
        return self.__task_id

    def as_xml(self):
        try:
            signal = int(self.signal())
        except ValueError:
            raise ValueError("signal must be an integer")
        if signal not in (0, 9, 15):
            raise ValueError("illegal signal: %r" % (signal))
        root, hdr, body = MessageBuilder.xml_parts()
        kill = etree.SubElement(body, self.tag)
        kill.attrib[XBE("signal")] = str(signal)
        etree.SubElement(kill, XBE("Task")).text = self.task_id()
        return root
    def from_xml(cls, root, hdr, body):
        kill = body.find(self.tag)
        if kill is None:
            raise MessageParserError("could not find 'Kill' element")
        task_id = kill.findtext(XBE("Task"))
        signal = kill.attrib[XBE("signal")]
        msg = Kill(task_id, signal)
        return msg
    from_xml = classmethod(from_xml)
MessageBuilder.register(Kill)

class StatusRequest(BaseClientMessage):
    """Request the status of a single task or all.

    body consists of 'StatusRequest' with a potential attribute
    'task-id' which identifies the desired task.
    """
    tag = XBE("StatusRequest")
    
    def __init__(self, task_id=None):
        BaseClientMessage.__init__(self)
        self.__task_id = task_id

    def task_id(self):
        return self.__task_id
    
    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        sr = etree.SubElement(body, self.tag)
        if self.task_id() is not None:
            sr.attrib[XBE("task-id")] = self.task_id()
        return root
    def from_xml(cls, root, hdr, body):
        sr = body.find(cls.tag)
        task_id = sr.attrib.get(XBE("task-id"))
        return cls(task_id)
    from_xml = classmethod(from_xml)
MessageBuilder.register(StatusRequest)

class StatusList(BaseServerMessage):
    """Answers the RequestStatus message.

    Holds a list of status information objects.
    """
    tag = XBE("StatusList")
    
    def __init__(self):
        BaseServerMessage.__init__(self)
        self.__entries = []

    def add(self, task):
        self.__entries.append({"TaskID": task.ID(),
                               "Submitted": task.tstamp})

    def entries(self):
        return self.__entries

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        entries = etree.SubElement(body, self.tag)
        for entry in self.__entries:
            e = etree.SubElement(entries, XBE("Status"))
            for key, value in entry.iteritems():
                etree.SubElement(e, XBE(key)).text = str(value)
        return root
    
    def from_xml(cls, root, hdr, body):
        cache_entries = cls()
        entries = body.find(cls.tag)
        for entry in entries:
            entry_info = {}
            for info_elem in entry:
                key = decodeTag(info_elem.tag)[1]
                value = info_elem.text
                entry_info[key] = value
            cache_entries.__entries.append(entry_info)
        return cache_entries
    from_xml = classmethod(from_xml)
MessageBuilder.register(StatusList)

#############################
#
#  instance/server messages
#
#############################

class InstanceMessage(SimpleMessage):
    pass

class InstanceAvailable(InstanceMessage):
    def __init__(self, id):
        InstanceMessage.__init__(self)

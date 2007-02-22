#!/usr/bin/env python
"""
The Xen Based Execution Environment XML Messages
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging, re
log = logging.getLogger(__name__)

from time import gmtime, strftime
from lxml import etree
from twisted.internet import defer, threads
from twisted.python import failure

from xbe.xml.namespaces import *
from xbe.xml import bes
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
        if klass.tag in MessageBuilder.builder_map.keys():
            raise RuntimeError("I already have a class registered with tag '%s'" % (klass.tag))
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

        @param xml_document a etree.Element or etree.ElementTree or something parsable to it
        @return the matching Message instance or a failure.Failure instance
        """
        # try to transform the given document into an etree instance
        if isinstance(xml_document, basestring):
            # got a string as an argument, so parse it
            try:
                xml_document = etree.fromstring(xml_document)
            except etree.XMLSyntaxError, e:
                raise MessageParserError("syntax error: %s" % e)
        if not isinstance(xml_document, (etree._Element, etree._ElementTree)):
            raise MessageParserError("the passed document must be an xml document")

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
    
    def as_str(self, *args, **kw):
        return etree.tostring(self.as_xml(), *args, **kw)

    def __str__(self):
        return self.as_str()

class SimpleMessage(Message):
    pass

class Error(SimpleMessage):
    ns  = XBE
    tag = ns("Error")
    
    def __init__(self, code=errcode.OK, msg=None):
        self.__info = errcode.info[code]
        self.__code = code
        self.__message = msg

    def code(self):
        return self.__code
    def message(self):
        return self.__message
    def name(self):
        return self.__info[0]
    def description(self):
        return self.__info[1]

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
	error = etree.SubElement(body, self.tag)
        
        error.attrib[Error.ns("code")] = str(self.code())
	etree.SubElement(error, self.ns("Name")).text = self.name()
        etree.SubElement(error, self.ns("Description")).text = self.description()
        if self.message() is not None:
            etree.SubElement(error, self.ns("Message")).text = self.message()
        return root

    def from_xml(cls, root, hdr, body):
        error = body.find(cls.tag)
        code = int(error.attrib[cls.ns("code")])
        msg = error.findtext(cls.ns("Message"))
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
    
    def __init__(self, task_id, signal=15):
        BaseClientMessage.__init__(self)
        if task_id is None:
            raise ValueError("task ID must not be None")
        self.__task_id = task_id
        self.__signal = int(signal)

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
        kill = body.find(cls.tag)
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

    def add(self, id, submitted_tstamp, state):
        self.__entries.append({"TaskID": id,
                               "Submitted": submitted_tstamp,
                               "State": state})

    def entries(self):
        return self.__entries

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        entries = etree.SubElement(body, self.tag)
        for entry in self.__entries:
            e = etree.SubElement(entries, XBE("Status"))
            etree.SubElement(e, XBE("TaskID")).text = entry["TaskID"]
            etree.SubElement(e, XBE("Submitted")).text = str(entry["Submitted"])
            etree.SubElement(e, XBE("State")).append(
                (bes.fromXBETaskState(entry["State"])))
        return root
    
    def from_xml(cls, root, hdr, body):
        status_list = cls()
        entries = body.find(cls.tag)
        for entry in entries:
            entry_info = {}
            entry_info["TaskID"] = entry.find(XBE("TaskID")).text
            entry_info["Submitted"] = entry.find(XBE("Submitted")).text
            entry_info["State"] = bes.toXBETaskState(entry.find(XBE("State"))[0])
            status_list.__entries.append(entry_info)
        return status_list
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
    """Notifys the daemon, that we (instance) are now available.

    body consists of 'InstanceAvailable' with the attribute 'inst-id'.

    Example:
    <InstanceAvailable inst-id='foo'>
       <NodeInformation>
          <Network>
             <IPList>
               <IP type="IPv{4,6}">first ip</IP>
               ...
             </IPList>
          </Network>
       </NodeInformation>
    </InstanceAvailable>
    """
    tag = XBE("InstanceAvailable")
    
    def __init__(self, inst_id):
        InstanceMessage.__init__(self)
        if inst_id is None:
            raise ValueError("instance ID must not be None")
        self.__inst_id = inst_id
        self.__ips = []

    def inst_id(self):
        return self.__inst_id

    def add_ip(self, ip):
        self.__ips.append(ip)
    def ips(self):
        return self.__ips
    
    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        ia = etree.SubElement(body, self.tag)
        if self.inst_id() is not None:
            ia.attrib[XBE("inst-id")] = self.inst_id()
        nodeinfo = etree.SubElement(ia, XBE("NodeInformation"))
        network = etree.SubElement(nodeinfo, XBE("Network"))
        iplist = etree.SubElement(network, XBE("IPList"))
        for ip in self.ips():
            etree.SubElement(iplist, XBE("IP")).text = ip
        return root

    def from_xml(cls, root, hdr, body):
        ia = body.find(cls.tag)
        inst_id = ia.attrib.get(XBE("inst-id"))
        obj = cls(inst_id)

        # ips
        map(obj.add_ip, [ip.text for ip in ia.findall(XBE("NodeInformation/Network/IPList/IP"))])
        return obj
    from_xml = classmethod(from_xml)
MessageBuilder.register(InstanceAvailable)

class InstanceAlive(InstanceMessage):
    """Notifies the daemon, that the instance is still alive.

    This message must be sent by an instance regularly to prevent the
    daemon from shutting down the instance.
    """
    tag = XBE("InstanceAlive")
    
    def __init__(self, inst_id, uptime=None):
        """Create a new InstanceAlive message.

        @param inst_id - the instance id in which the task has been running
        """
        InstanceMessage.__init__(self)
        if inst_id is None:
            raise ValueError("I need at least an instance-ID!")
        self.__inst_id = inst_id
        self.__uptime = uptime and int(uptime)

    def inst_id(self):
        return self.__inst_id
    def uptime(self):
        return self.__uptime
    
    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        ia = etree.SubElement(body, self.tag)
        ia.attrib[XBE("inst-id")] = self.inst_id()
        if self.uptime() is not None:
            etree.SubElement(ia, XBE("Uptime")).text = str(self.uptime())
        return root

    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        inst_id = elem.attrib[XBE("inst-id")]
        uptime = elem.findtext(XBE("Uptime"))
        return cls(inst_id, uptime)
    from_xml = classmethod(from_xml)
MessageBuilder.register(InstanceAlive)

class TaskFinished(InstanceMessage):
    """Notifies the daemon, that the task has finished.

    The message does not indicate, whether the job failed or not, but
    it contains its exitcode and other stuff.
    """
    tag = XBE("TaskFinished")
    
    def __init__(self, inst_id, exitcode, task_id=None):
        """Create a new TaskFinished message.

        @param inst_id - the instance id in which the task has been running
        @param task_id - if the instance does know the task_id, it may be set here.
        """
        InstanceMessage.__init__(self)
        if inst_id is None:
            raise ValueError("I need at least an instance-ID!")
        self.__inst_id = inst_id
        self.__task_id = task_id
        self.__exitcode = int(exitcode)

    def inst_id(self):
        return self.__inst_id
    def task_id(self):
        return self.__task_id
    def exitcode(self):
        return self.__exitcode
    
    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        tf = etree.SubElement(body, self.tag)
        tf.attrib[XBE("inst-id")] = self.inst_id()
        if self.task_id() is not None:
            tf.attrib[XBE("task-id")] = self.task_id()
        etree.SubElement(tf, XBE("ExitCode")).text = str(self.exitcode())
        return root

    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        inst_id = elem.attrib[XBE("inst-id")]
        task_id = elem.attrib.get(XBE("task-id"))
        exitcode = int(elem.findtext(XBE("ExitCode")))
        return cls(inst_id, exitcode, task_id)
    from_xml = classmethod(from_xml)
MessageBuilder.register(TaskFinished)

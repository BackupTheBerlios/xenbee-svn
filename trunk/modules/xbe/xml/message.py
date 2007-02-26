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
        
        error.attrib["code"] = str(self.code())
	etree.SubElement(error, self.ns("Name")).text = self.name()
        etree.SubElement(error, self.ns("Description")).text = self.description()
        if self.message() is not None:
            etree.SubElement(error, self.ns("Message")).text = self.message()
        return root

    def from_xml(cls, root, hdr, body):
        error = body.find(cls.tag)
        code = int(error.attrib["code"])
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

class ReservationRequest(BaseClientMessage):
    """Sends a request for a reservation.

    not sure about meta information

    <ReservationRequest/>
    """
    tag = XBE("ReservationRequest")
    
    def __init__(self):
        BaseClientMessage.__init__(self)

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        elem = etree.SubElement(body, self.tag)
        return root
    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        if elem is None:
            raise MessageParserError("could not find 'ReservationRequest' element")
        return cls()
    from_xml = classmethod(from_xml)
MessageBuilder.register(ReservationRequest)

class ReservationResponse(BaseServerMessage):
    """Response to a ReservationRequest request.

    not sure about *all* meta information
    """
    tag = XBE("ReservationResponse")
    
    def __init__(self, ticket, task_id):
        BaseServerMessage.__init__(self)
        self.__ticket = ticket
        self.__task_id = task_id

    def ticket(self):
        return self.__ticket
    def task_id(self):
        return self.__task_id
    
    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        elem = etree.SubElement(body, self.tag)
        elem.attrib["task-id"] = self.task_id()
        reservation = etree.SubElement(elem, XBE("Reservation"))
        etree.SubElement(reservation, XBE("Ticket")).text = self.ticket()
        return root
    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        if elem is None:
            raise MessageParserError("could not find 'ReservationResponse' element")
        task_id = elem.attrib.get("task-id")
        ticket = elem.findtext(XBE("Reservation/Ticket"))
        if ticket is None:
            raise MessageParserError("no 'Ticket' found!")
        return cls(ticket, task_id)
    from_xml = classmethod(from_xml)
MessageBuilder.register(ReservationResponse)

class ConfirmReservation(BaseClientMessage):
    """Client confirmed the reservation.

    The confirmation message consists of a JSDL document with the
    ticket as an additional resource.
    """
    tag = XBE("ConfirmReservation")

    def __init__(self, ticket, jsdl, start_task=True):
        BaseClientMessage.__init__(self)
        self.__jsdl = jsdl
        self.__ticket = ticket
        self.__start_task = start_task

    def jsdl(self):
        return self.__jsdl

    def ticket(self):
        return self.__ticket

    def start_task(self):
        return self.__start_task

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        elem = etree.SubElement(body, self.tag)
        if self.start_task():
            elem.attrib["start-task"] = "true"
        elem.append(self.__jsdl)
        resources = self.__jsdl.find(JSDL("JobDescription/Resources"))
        if resources is None:
            resources = etree.SubElement(self.__jsdl, JSDL("Resources"))
        reservation = etree.SubElement(resources, XBE("Reservation"))
        etree.SubElement(reservation, XBE("Ticket")).text = self.__ticket
        return root

    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        if elem is None:
            raise MessageParserError("could not find 'ConfirmReservation' element")
        start_task = elem.attrib.get("start-task")
        if start_task in ("true", "1"):
            start_task = True
        else:
            start_task = False
        jsdl = elem.find(JSDL("JobDefinition"))
        if jsdl is None:
            raise MessageParserError("could not find 'JobDefinition' element")
        resources = jsdl.find(JSDL("JobDescription/Resources"))
        if resources is None:
            raise MessageParserError("could not find 'Resources' element")
        ticket = resources.findtext(XBE("Reservation/Ticket"))
        return cls(ticket, jsdl, start_task)
    from_xml = classmethod(from_xml)
MessageBuilder.register(ConfirmReservation)
        
class CancelReservation(BaseClientMessage):
    """Client cancels a reservation.

    The cancel message consists of a xbe:Reservation element which
    contains the ticket information.
    """
    tag = XBE("CancelReservation")

    def __init__(self, ticket):
        BaseClientMessage.__init__(self)
        self.__ticket = ticket

    def ticket(self):
        return self.__ticket

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        elem = etree.SubElement(body, self.tag)
        reservation = etree.SubElement(elem, XBE("Reservation"))
        etree.SubElement(reservation, XBE("Ticket")).text = self.__ticket
        return root

    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        if elem is None:
            raise MessageParserError("could not find 'CancelReservation' element")
        ticket = elem.findtext(XBE("Reservation/Ticket"))
        return cls(ticket)
    from_xml = classmethod(from_xml)
MessageBuilder.register(CancelReservation)

class ConfirmAck(BaseServerMessage):
    """Acknowledgement of the Confirm message."""
    tag = XBE("ConfirmAck")

    def __init__(self, ticket, task_id):
        BaseServerMessage.__init__(self)
        self.__task_id = task_id
        self.__ticket = ticket

    def task_id(self):
        return self.__task_id
    def ticket(self):
        return self.__ticket

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        elem = etree.SubElement(body, self.tag)
        elem.attrib["task-id"] = self.task_id()
        reservation = etree.SubElement(elem, XBE("Reservation"))
        etree.SubElement(reservation, XBE("Ticket")).text = self.__ticket
        return root

    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        if elem is None:
            raise MessageParserError("could not find 'ConfirmAck' element")
        ticket = elem.findtext(XBE("Reservation/Ticket"))
        task_id = elem.attrib["task-id"]
        return cls(task_id, ticket)
    from_xml = classmethod(from_xml)
MessageBuilder.register(ConfirmAck)

class StartRequest(BaseClientMessage):
    """Request the start of a task."""
    tag = XBE("StartRequest")

    def __init__(self, task_id):
        BaseClientMessage.__init__(self)
        self.__task_id = task_id

    def task_id(self):
        return self.__task_id

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        elem = etree.SubElement(body, self.tag)
        elem.attrib["task-id"] = self.task_id()
        reservation = etree.SubElement(elem, XBE("Reservation"))
        etree.SubElement(reservation, XBE("Ticket")).text = self.__ticket
        return root

    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        if elem is None:
            raise MessageParserError("could not find 'StartRequest' element")
        ticket = elem.findtext(XBE("Reservation/Ticket"))
        task_id = elem.attrib["task-id"]
        return cls(task_id, ticket)
    from_xml = classmethod(from_xml)
MessageBuilder.register(StartRequest)

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
        kill.attrib["signal"] = str(signal)
        etree.SubElement(kill, XBE("Task")).text = self.task_id()
        return root
    def from_xml(cls, root, hdr, body):
        kill = body.find(cls.tag)
        if kill is None:
            raise MessageParserError("could not find 'Kill' element")
        task_id = kill.findtext(XBE("Task"))
        signal = kill.attrib["signal"]
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
            sr.attrib["task-id"] = self.task_id()
        return root
    def from_xml(cls, root, hdr, body):
        sr = body.find(cls.tag)
        task_id = sr.attrib.get("task-id")
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
            ia.attrib["inst-id"] = self.inst_id()
        nodeinfo = etree.SubElement(ia, XBE("NodeInformation"))
        network = etree.SubElement(nodeinfo, XBE("Network"))
        iplist = etree.SubElement(network, XBE("IPList"))
        for ip in self.ips():
            etree.SubElement(iplist, XBE("IP")).text = ip
        return root

    def from_xml(cls, root, hdr, body):
        ia = body.find(cls.tag)
        inst_id = ia.attrib.get("inst-id")
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
        ia.attrib["inst-id"] = self.inst_id()
        if self.uptime() is not None:
            etree.SubElement(ia, XBE("Uptime")).text = str(self.uptime())
        return root

    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        inst_id = elem.attrib["inst-id"]
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
        tf.attrib["inst-id"] = self.inst_id()
        if self.task_id() is not None:
            tf.attrib["task-id"] = self.task_id()
        etree.SubElement(tf, XBE("ExitCode")).text = str(self.exitcode())
        return root

    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        inst_id = elem.attrib["inst-id"]
        task_id = elem.attrib.get("task-id")
        exitcode = int(elem.findtext(XBE("ExitCode")))
        return cls(inst_id, exitcode, task_id)
    from_xml = classmethod(from_xml)
MessageBuilder.register(TaskFinished)

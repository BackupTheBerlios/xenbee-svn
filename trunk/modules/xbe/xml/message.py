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

class EstablishMLS(Message):
    """Represents a certificate.

    it only contains a header, that holds a signed X509 certificate.
    see xml.security.X509SecurityLayer for information about signing.
    """
    tag = XBE("EstablishMLS")

    ST_DISCONNECTED = "disconnected"
    ST_ESTABLISHED  = "established"
    
    def __init__(self, securityLayer, state):
        Message.__init__(self)
        self.__securityLayer = securityLayer
        self.__state = state

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        emls = etree.SubElement(body, XBE("EstablishMLS"))
        emls.attrib["state"] = self.__state
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
        for entry in entries.getchildren():
            entry_info = {}
            for info_elem in entry.getchildren():
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

class TerminateRequest(BaseClientMessage):
    """Client sends a terminate request."""
    tag = XBE("TerminateRequest")

    def __init__(self, ticket):
        BaseClientMessage.__init__(self)
        if ticket is None:
            raise ValueError("ticket must not be None")
        self.__ticket = str(ticket)

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
            raise MessageParserError("could not find 'TerminateRequest' element")
        ticket = elem.findtext(XBE("Reservation/Ticket"))
        if ticket is None:
            raise MessageParserError("could not find Reservation information")
        return cls(ticket)
    from_xml = classmethod(from_xml)
MessageBuilder.register(TerminateRequest)

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
class StatusRequest(BaseClientMessage):
    """Request the status of a single task or all.

    body consists of 'StatusRequest' with a potential attribute
    'task-id' which identifies the desired task.
    """
    tag = XBE("StatusRequest")
    
    def __init__(self, ticket):
        BaseClientMessage.__init__(self)
        self.__ticket = str(ticket)

    def ticket(self):
        return self.__ticket
    
    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        sr = etree.SubElement(body, self.tag)
        reservation = etree.SubElement(sr, XBE("Reservation"))
        etree.SubElement(reservation, XBE("Ticket")).text = self.ticket()
        return root
    def from_xml(cls, root, hdr, body):
        sr = body.find(cls.tag)
        ticket = sr.find(XBE("Reservation/Ticket"))
        return cls(ticket)
    from_xml = classmethod(from_xml)
MessageBuilder.register(StatusRequest)

class StatusList(BaseServerMessage):
    """Answers the RequestStatus message.

    Holds a list of status information objects.

    <StatusList>
      <Status task-id="...">
        <bes-state>...
        <Meta>
           <Info key="...">value</Info>
        </Meta>
    """
    tag = XBE("StatusList")
    
    def __init__(self):
        BaseServerMessage.__init__(self)
        self.__entries = []

    def add(self, id, state, meta={}):
        self.__entries.append({"TaskID": id,
                               "State": state,
                               "Meta": meta})

    def entries(self):
        return self.__entries

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        entries = etree.SubElement(body, self.tag)
        for entry in self.__entries:
            e = etree.SubElement(entries, XBE("Status"))
            e.attrib["task-id"] = entry["TaskID"]
            e.append(bes.fromXBETaskState(entry["State"]))
            meta = etree.SubElement(e, XBE("Meta"))
            for k, v in entry["Meta"].iteritems():
                info = etree.SubElement(meta, XBE("Info"))
                info.attrib["key"] = k
                info.text = str(v)
        return root
    
    def from_xml(cls, root, hdr, body):
        status_list = cls()
        entries = body.find(cls.tag)
        for entry in entries.getchildren():
            entry_info = {}
            entry_info["TaskID"] = entry.attrib["task-id"]
            entry_info["State"] = bes.toXBETaskState(
                entry.find(BES_ACTIVITY("ActivityStatus")))
            meta = {}
            for info in entry.findall(XBE("Meta/Info")):
                k = info.attrib["key"]
                v = (info.text or "").strip()
                meta[k] = v
            entry_info["Meta"] = meta
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
               <IP>127.0.0.1</IP>
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
        map(obj.add_ip,
            [ip.text for ip in ia.findall(XBE("NodeInformation/Network/IPList/IP"))])
        return obj
    from_xml = classmethod(from_xml)
MessageBuilder.register(InstanceAvailable)

class InstanceAlive(InstanceMessage):
    """Notifies the daemon, that the instance is still alive.

    This message must be sent by an instance regularly to prevent the
    daemon from shutting down the instance.
    """
    tag = XBE("InstanceAlive")
    
    def __init__(self, inst_id, uptime=None, idle=None):
        """Create a new InstanceAlive message.

        @param inst_id - the instance id in which the task has been running
        """
        InstanceMessage.__init__(self)
        if inst_id is None:
            raise ValueError("I need at least an instance-ID!")
        self.__inst_id = inst_id
        self.__uptime = uptime and int(uptime)
        self.__idle = idle and int(idle)

    def inst_id(self):
        return self.__inst_id
    def uptime(self):
        return self.__uptime
    def idle(self):
        return self.__idle
    
    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        ia = etree.SubElement(body, self.tag)
        ia.attrib["inst-id"] = self.inst_id()
        if self.uptime() is not None:
            etree.SubElement(ia, XBE("Uptime")).text = str(self.uptime())
        if self.idle() is not None:
            etree.SubElement(ia, XBE("Idle")).text = str(self.idle())
        return root

    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        inst_id = elem.attrib["inst-id"]
        uptime = elem.findtext(XBE("Uptime"))
        idle = elem.findtext(XBE("Idle"))
        return cls(inst_id, uptime, idle)
    from_xml = classmethod(from_xml)
MessageBuilder.register(InstanceAlive)

class ExecutionFinished(InstanceMessage):
    """Notifies the daemon, that the task has finished.

    The message does not indicate, whether the job failed or not, but
    it contains its exitcode and other stuff.
    """
    tag = XBE("ExecutionFinished")
    
    def __init__(self, inst_id, exitcode, task_id=None):
        """Create a new ExecutionFinished message.

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
MessageBuilder.register(ExecutionFinished)

class ExecutionFailed(InstanceMessage):
    """Notifies the daemon, that the task has failed.

    This message is sent, when the task could not be executed due to
    some reason.
    """
    tag = XBE("ExecutionFailed")
    
    def __init__(self, inst_id, reason):
        """Create a new ExecutionFinished message.

        @param inst_id - the instance id in which the task has been running
        @param task_id - if the instance does know the task_id, it may be set here.
        """
        InstanceMessage.__init__(self)
        if inst_id is None:
            raise ValueError("I need at least an instance-ID!")
        self.__inst_id = inst_id
        self.__reason = int(reason)
        
    def inst_id(self):
        return self.__inst_id
    def reason(self):
        return self.__reason
    
    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        tf = etree.SubElement(body, self.tag)
        tf.attrib["inst-id"] = self.inst_id()
        tf.attrib["reason"] = str(self.reason())
        return root

    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        inst_id = elem.attrib["inst-id"]
        reason = elem.attrib["reason"]
        return cls(inst_id, reason)
    from_xml = classmethod(from_xml)
MessageBuilder.register(ExecutionFailed)

class InstanceShuttingDown(InstanceMessage):
    """Notifies the daemon, that the instance is going down.
    """
    tag = XBE("InstanceShuttingDown")
    
    def __init__(self, inst_id, signal):
        """Create a new InstanceShuttingDown message.

        @param inst_id the usual instance id
        @param signal the signal due to which the instance is going down
        """
        InstanceMessage.__init__(self)
        if inst_id is None:
            raise ValueError("I need at least an instance-ID!")
        self.__inst_id = inst_id
        self.__signal = signal

    def inst_id(self):
        return self.__inst_id
    def signal(self):
        return self.__signal
    
    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        xml = etree.SubElement(body, self.tag)
        xml.attrib["inst-id"] = self.inst_id()
        xml.attrib["signal"] = str(self.signal())
        return root

    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        inst_id = elem.attrib["inst-id"]
        signal = int(elem.attrib["signal"])
        return cls(inst_id, signal)
    from_xml = classmethod(from_xml)
MessageBuilder.register(InstanceShuttingDown)

class ExecuteTask(BaseServerMessage):
    """Execute a task on an instance.

    The ExecuteTask consists of a JSDL document.
    """
    tag = XBE("ExecuteTask")

    def __init__(self, jsdl, task_id):
        BaseServerMessage.__init__(self)
        self.__jsdl = jsdl
        self.__task_id = task_id

    def jsdl(self):
        return self.__jsdl

    def task_id(self):
        return self.__task_id

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        elem = etree.SubElement(body, self.tag)
        elem.attrib["task-id"] = str(self.task_id())
        elem.append(self.__jsdl)
        return root

    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        if elem is None:
            raise MessageParserError("could not find 'ExecuteTask' element")
        task_id = elem.attrib["task-id"]
        jsdl = elem.find(JSDL("JobDefinition"))
        if jsdl is None:
            raise MessageParserError("could not find 'JobDefinition' element")
        return cls(jsdl, task_id)
    from_xml = classmethod(from_xml)
MessageBuilder.register(ExecuteTask)

# XenBEE is a software that provides execution of applications
# in self-contained virtual disk images on a remote host featuring
# the Xen hypervisor.
#
# Copyright (C) 2007 Alexander Petry <petry@itwm.fhg.de>.
# This file is part of XenBEE.

# XenBEE is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# XenBEE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA

"""
The Xen Based Execution Environment XML Messages
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging, re, types
log = logging.getLogger(__name__)

from time import gmtime, strftime
from pprint import pformat
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
                if hasattr(etree, 'clearErrorLog'): etree.clearErrorLog()
                if hasattr(etree, 'clear_error_log'): etree.clear_error_log()
                xml_document = etree.fromstring(xml_document)
            except etree.XMLSyntaxError, e:
                raise MessageParserError("syntax error", e)
        if not isinstance(xml_document, (etree._Element, etree._ElementTree)):
            raise MessageParserError("the passed document must be an xml document")

        root, hdr, body = MessageBuilder.xml_parts(xml_document)
        if body is None or not len(body):
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
        self.__code = int(code)
        self.__message = msg

    def __repr__(self):
        return "<%(cls)s %(code)d [%(name)s] - %(desc)s>" % {
            "cls": self.__class__.__name__,
            "code": self.code(),
            "name": self.name(),
            "desc": self.description(),
        }

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
        self.__entries = {}

    def __repr__(self):
        return "<%(cls)s with %(num)d entr%(plural_s)s:\n%(entries)s\n>" % {
            "cls": self.__class__.__name__,
            "num": len(self.__entries),
            "plural_s": len(self.__entries) == 1 and "y" or "ies",
            "entries": pformat(self.__entries),
        }

    def add(self, uri, meta={}):
        self.__entries[uri] = meta

    def entries(self):
        return self.__entries

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        entries = etree.SubElement(body, self.tag)

        for uri, meta_info in self.__entries.iteritems():
            e = etree.SubElement(entries, XBE("Entry"))
            etree.SubElement(e, XBE("URI")).text = uri
            meta = etree.SubElement(e, XBE("Meta"))
            unparse_dictionary(meta_info, meta)
        return root
    
    def from_xml(cls, root, hdr, body):
        cache_entries = cls()
        entries = body.find(cls.tag)
        for entry in entries.getchildren():
            uri = entry.findtext(XBE("URI"))
            meta = parse_dictionary(entry.find(XBE("Meta/Dict")), {})
            cache_entries.add(uri, meta)
        return cache_entries
    from_xml = classmethod(from_xml)
MessageBuilder.register(CacheEntries)

class CacheFile(BaseClientMessage):
    """Sends a request for caching a file.

    - uri the file to cache

    - hash which represents the hash-value of
      the file (this will also be stored)

    - description some meaningful description of that file
    - type one of "image", "kernel", "initrd", "data"
    """
    tag = XBE("CacheFile")
    
    def __init__(self, uri, type, desc, hash_value=None, hash_algo=None):
        BaseClientMessage.__init__(self)
        self.__uri = uri
        if type not in ("image", "kernel", "initrd", "data"):
            raise ValueError("illegal value for 'type'", type)
        self.__type = type
        self.__desc = desc

        if hash_value is not None:
            from xbe.xml.jsdl import HashValidator
            self.__validator = HashValidator(hash_value, hash_algo)
        else:
            self.__validator = None

    def uri(self):
        return self.__uri
    def validator(self):
        return self.__validator
    def type_of_file(self):
        return self.__type
    def description(self):
        return self.__desc

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        elem = etree.SubElement(body, self.tag)
        elem.attrib["type"] = self.type_of_file()
        loc = etree.SubElement(elem, XSDL("Location"))
        etree.SubElement(loc, XSDL("URI")).text = self.uri()
        if self.validator() is not None:
            hv = etree.SubElement(loc, XSDL("Hash"))
            hv.text =  self.validator().hexdigest()
            hv.attrib["algorithm"] = self.validator().algorithm()
        etree.SubElement(elem, XSDL("Description")).text = self.description()
        return root
    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        if elem is None:
            raise MessageParserError("could not find 'CacheFile' element")
        tof = elem.attrib["type"]
        uri = elem.findtext(XSDL("Location/URI"))
        desc = elem.findtext(XSDL("Description"))
        h = elem.find(XSDL("Location/Hash"))
        if h is not None:
            ha = h.attrib.get("algorithm", "sha1")
            hd = h.text
        else:
            ha = None
            hd = None
        return cls(uri, tof, desc, hd, ha)
    from_xml = classmethod(from_xml)
MessageBuilder.register(CacheFile)
    
class CacheRemove(BaseClientMessage):
    """Sends a request for removing a cached file.

    - uri the entry that is to be removed
    """
    tag = XBE("CacheRemove")
    
    def __init__(self, uri):
        BaseClientMessage.__init__(self)
        self.__uri = uri

    def uri(self):
        return self.__uri

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        elem = etree.SubElement(body, self.tag)
        etree.SubElement(elem, XSDL("URI")).text = self.uri()
        return root
    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        uri = elem.findtext(XSDL("URI"))
        return cls(uri)
    from_xml = classmethod(from_xml)
MessageBuilder.register(CacheRemove)

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
        self.__jsdl       = jsdl
        self.__ticket     = ticket
        self.__start_task = start_task
        self.__uuid       = "none"

    def jsdl(self):
        return self.__jsdl

    def ticket(self):
        return self.__ticket

    def start_task(self):
        return self.__start_task

    def uuid(self):
        return self.__uuid
    
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

    def __init__(self, ticket, reason="UserCancel", remove_entry=False):
        BaseClientMessage.__init__(self)
        if ticket is None:
            raise ValueError("ticket must not be None")
        self.__ticket = str(ticket)
        self.__reason = str(reason)
        self.__remove_entry = remove_entry

    def ticket(self):
        return self.__ticket

    def removeEntry(self):
        return self.__remove_entry

    def reason(self):
        return self.__reason
    
    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        elem = etree.SubElement(body, self.tag)
        elem.attrib["remove-entry"] = self.removeEntry() and "1" or "0"
        etree.SubElement(elem, XBE("Reason")).text = self.reason()
        reservation = etree.SubElement(elem, XBE("Reservation"))
        etree.SubElement(reservation, XBE("Ticket")).text = self.ticket()
        return root

    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        if elem is None:
            raise MessageParserError("could not find 'TerminateRequest' element")
        remove = str(elem.attrib.get("remove-entry")).lower() in ["1", "yes", "true"]
        ticket = elem.findtext(XBE("Reservation/Ticket"))
        if ticket is None:
            raise MessageParserError("could not find Reservation information")
        reason = elem.findtext(XBE("Reason")) or ""
        return cls(ticket, reason, remove)
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
        return cls(ticket, task_id)
    from_xml = classmethod(from_xml)
MessageBuilder.register(ConfirmAck)

class StartRequest(BaseClientMessage):
    """Request the start of a task."""
    tag = XBE("StartRequest")

    def __init__(self, ticket):
        BaseClientMessage.__init__(self)
        self.__ticket = ticket

    def ticket(self):
        return self.__ticket

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        elem = etree.SubElement(body, self.tag)
        reservation = etree.SubElement(elem, XBE("Reservation"))
        etree.SubElement(reservation, XBE("Ticket")).text = self.ticket()
        return root

    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        if elem is None:
            raise MessageParserError("could not find 'StartRequest' element")
        ticket = elem.findtext(XBE("Reservation/Ticket"))
        return cls(ticket)
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
    
    def __init__(self, ticket, remove_entry=False, execute_status_task=False):
        BaseClientMessage.__init__(self)
        self.__ticket = str(ticket)
        self.__remove_entry = remove_entry
        self.__execute_status_task = execute_status_task

    def ticket(self):
        return self.__ticket

    def removeEntry(self):
        return self.__remove_entry

    def execute_status_task(self):
        return self.__execute_status_task
    
    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        sr = etree.SubElement(body, self.tag)
        sr.attrib["remove-entry"] = self.removeEntry() and "1" or "0"
        sr.attrib["execute-status-task"] = self.execute_status_task() and "1" or "0"
        reservation = etree.SubElement(sr, XBE("Reservation"))
        etree.SubElement(reservation, XBE("Ticket")).text = self.ticket()
        return root
    def from_xml(cls, root, hdr, body):
        sr = body.find(cls.tag)
        remove = str(sr.attrib.get("remove-entry")).lower() in ["1", "yes", "true"]
        execute = str(sr.attrib.get("execute-status-task")).lower() in ["1", "yes", "true"]
        ticket = sr.findtext(XBE("Reservation/Ticket"))
        return cls(ticket, remove, execute)
    from_xml = classmethod(from_xml)
MessageBuilder.register(StatusRequest)

def parse_dictionary(elem, dictionary):
    for entry in elem.iterchildren(tag=XBE("Entry")):
        key = entry.attrib["key"]
        if len(entry.getchildren()):
            value = parse_dictionary(entry[0], {})
        else:
            value = (entry.text or "").strip()
        dictionary[key] = value
    return dictionary

def unparse_dictionary(dictionary, parent):
    d = etree.SubElement(parent, XBE("Dict"))
    for k, v in dictionary.iteritems():
        entry = etree.SubElement(d, XBE("Entry"))
        entry.attrib["key"] = str(k)
        if type(v) == types.DictType:
            unparse_dictionary(v, entry)
        else:
            entry.text = str(v)

class StatusList(BaseServerMessage):
    """Answers the RequestStatus message.

    Holds a list of status information objects.

    <StatusList>
      <Status task-id="...">
        <bes-state>...
        <Meta>
           <Dict><Entry key="...">value</Entry></Dict>
        </Meta>
    """
    tag = XBE("StatusList")
    
    def __init__(self):
        BaseServerMessage.__init__(self)
        self.__entries = {}

    def __repr__(self):
        return "<%(cls)s with %(num)d entr%(plural_s)s:\n%(entries)s\n>" % {
            "cls": self.__class__.__name__,
            "num": len(self.__entries),
            "plural_s": len(self.__entries) == 1 and "y" or "ies",
            "entries": pformat(self.__entries),
        }

    def add(self, taskid, state, ticket, meta={}):
        self.__entries[taskid] = { "State": state,
				   "Ticket": ticket,
                                   "Meta": meta }

    def entries(self):
        return self.__entries

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        entries = etree.SubElement(body, self.tag)
        for task_id, info in self.__entries.iteritems():
            e = etree.SubElement(entries, XBE("Status"))
            e.attrib["task-id"] = task_id
            e.append(bes.fromXBETaskState(info["State"]))
            etree.SubElement(e, XBE("Ticket")).text = info["Ticket"]
            meta = etree.SubElement(e, XBE("Meta"))
            unparse_dictionary(info["Meta"], meta)
        return root
    
    def from_xml(cls, root, hdr, body):
        status_list = cls()
        entries = body.find(cls.tag)
        for entry in entries.findall(XBE("Status")):
            task_id = entry.attrib["task-id"]
            state = bes.toXBETaskState(entry.find(
                BES_ACTIVITY("ActivityStatus")))
            ticket = entry.findtext(XBE("Ticket"))
            meta = parse_dictionary(entry.find(XBE("Meta/Dict")), {})
            status_list.add(task_id, state, ticket, meta)
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
        """Create a new ExecutionFailed message.

        @param inst_id - the instance id in which the task has been running
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

class TerminateTask(BaseServerMessage):
    """Terminate the executing task."""
    tag = XBE("TerminateTask")

    def __init__(self, task_id):
        BaseServerMessage.__init__(self)
        self.__task_id = task_id

    def task_id(self):
        return self.__task_id

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        elem = etree.SubElement(body, self.tag)
        elem.attrib["task-id"] = str(self.task_id())
        return root

    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        if elem is None:
            raise MessageParserError("could not find 'TerminateTask' element")
        task_id = elem.attrib["task-id"]
        return cls(task_id)
    from_xml = classmethod(from_xml)
MessageBuilder.register(TerminateTask)

## calana extensions
class PollRequest(BaseClientMessage):
    """Sends a poll request for last command.
    <PollRequest cmd-name=''>
    </PollRequest>
    """
    tag = XBE("PollRequest")
    
    def __init__(self, cmdname):
        BaseClientMessage.__init__(self)
        if cmdname is None:
            raise MessageParserError("could not initialize PollRequest")
        self.__cmd_name = cmdname

    def cmd_name(self):
        return self.__cmd_name
    
    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        elem = etree.SubElement(body, self.tag)
        if self.cmd_name() is None:
            elem.attrib["cmd-name"] = "NNN"
        else:
            elem.attrib["cmd-name"] = self.cmd_name()
        etree.SubElement(elem, XBE("Poll_Req"))

        mymsg = etree.tostring(root, xml_declaration=True)
        log.debug("XML '%s'" % mymsg)
        return root
    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        if elem is None:
            raise MessageParserError("could not find 'PollRequest' element")
        cmd_name = elem.attrib.get("cmd-name")
        return cls(cmd_name)
    from_xml = classmethod(from_xml)
MessageBuilder.register(PollRequest)

class PollResponse(BaseServerMessage):
    """Response to a ping request.
    <PollResponse cmd_name=''>
    </PollResponse>
    """
    tag = XBE("PollResponse")
    
    def __init__(self, uuid, cmdname):
        BaseServerMessage.__init__(self)
        self.__uuid     = uuid
        self.__cmd_name = cmdname

    def uuid(self):
        return self.__uuid
    
    def cmd_name(self):
        return self.__cmd_name
    
    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        elem = etree.SubElement(body, self.tag)
        elem.attrib["uuid"] = self.uuid()
        elem.attrib["cmd-name"] = self.cmd_name()
        return root
    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        if elem is None:
            raise MessageParserError("could not find 'PingResponse' element")
        uuid     = elem.attrib["uuid"]
        cmd_name = elem.attrib["cmd-name"]
        return cls(uuid, cmd_name)
    from_xml = classmethod(from_xml)
MessageBuilder.register(PollResponse)

class PingRequest(BaseClientMessage):
    """Sends a ping request.
    <PingRequest/>
    """
    tag = XBE("PingRequest")
    
    def __init__(self, uuid=None):
        BaseClientMessage.__init__(self)
        if uuid is None:
            self.__uuid = "None"
        else:
            self.__uuid = uuid

    def uuid(self):
        return self.__uuid
    
    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        elem = etree.SubElement(body, self.tag)
        elem.attrib["uuid"] = self.uuid()
        etree.SubElement(elem, XBE("Ping_1"))

        mymsg = etree.tostring(root, xml_declaration=True)
        log.debug("XML '%s'" % mymsg)
        return root
    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        if elem is None:
            raise MessageParserError("could not find 'PingRequest' element")
        uuid     = elem.attrib["uuid"]
        return cls(uuid)
    from_xml = classmethod(from_xml)
MessageBuilder.register(PingRequest)

class PongResponse(BaseServerMessage):
    """Response to a ping request.
    <PongResponse/>
    """
    tag = XBE("PongResponse")
    
    def __init__(self, uuid, count=0):
        BaseServerMessage.__init__(self)
        self.__uuid  = uuid
        self.__count = count

    def uuid(self):
        return self.__uuid
    
    def count(self):
        return self.__count
    
    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        elem = etree.SubElement(body, self.tag)
        elem.attrib["uuid"] = self.uuid()
        elem.attrib["count"] = str(self.count())
        return root
    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        if elem is None:
            raise MessageParserError("could not find 'PingResponse' element")
        uuid     = elem.attrib["uuid"]
        count    = elem.attrib["count"]
        return cls(uuid, count)
    from_xml = classmethod(from_xml)
MessageBuilder.register(PongResponse)

class XbedAvailable(BaseServerMessage):
    """Notifys the broker, that we (xbed daemon) are now available.

    body consists of 'XbedAvailable' with the attribute 'inst-id'.

    Example:
    <XbedAvailable xbed-id='foo'>
    </XbedAvailable>
    """
    tag = XBE("XbedAvailable")
    
    def __init__(self, xbed_id):
        BaseServerMessage.__init__(self)
        if xbed_id is None:
            raise ValueError("XBE Daemon ID must not be None")
        self.__xbed_id = 1#inst_id

    def xbed_id(self):
        return self.__xbed_id

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        ia = etree.SubElement(body, self.tag)
        #if self.inst_id() is not None:
        ia.attrib["xbed-id"] = "1" #self.xbed_id()
        return root

    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        if elem is None:
            raise MessageParserError("could not find 'XbedAvailable' element")
        xbed_id = elem.attrib.get("xbed-id")
        return cls(xbed_id)
        #return cls()
    from_xml = classmethod(from_xml)
MessageBuilder.register(XbedAvailable)

class XbedAlive(BaseServerMessage):
    """Notifies the broker, that the xbe daemon is still alive.

    This message must be sent by an xbe daemon regularly to prevent the
    daemon from shutting down the xbe daemon.

    Example:
    <XbedAlive xbed-id='foo'>
    </XbedAlive>
    """
    tag = XBE("XbedAlive")
    
    def __init__(self, xbed_id, uptime=None, idle=None):
        """Create a new XbedAlive message.

        @param xbed_id - the xbed id in which the task has been running
        """
        BaseServerMessage.__init__(self)
        if xbed_id is None:
            raise ValueError("I need at least an instance-ID!")
        self.__xbed_id = "1" #inst_id
        self.__uptime = uptime and int(uptime)
        self.__idle = idle and int(idle)

    def xbed_id(self):
        return self.__xbed_id
    def uptime(self):
        return self.__uptime
    def idle(self):
        return self.__idle
    
    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        ia = etree.SubElement(body, self.tag)
        ia.attrib["xbed-id"] = self.xbed_id()
        if self.uptime() is not None:
            etree.SubElement(ia, XBE("Uptime")).text = str(self.uptime())
        if self.idle() is not None:
            etree.SubElement(ia, XBE("Idle")).text = str(self.idle())
        return root

    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        xbed_id = elem.attrib["xbed-id"]
        uptime  = elem.findtext(XBE("Uptime"))
        idle    = elem.findtext(XBE("Idle"))
        return cls(xbed_id, uptime, idle)
    #return cls()
    from_xml = classmethod(from_xml)
MessageBuilder.register(XbedAlive)

class BookingRequest(BaseClientMessage):
    """Sends a ping request.
    <BookingRequest/>
    """
    tag = XBE("BookingRequest")
    
    def __init__(self, uuid=None):
        BaseClientMessage.__init__(self)
        if uuid is None:
            self.__uuid = "None"
        else:
            self.__uuid = uuid

    def uuid(self):
        return self.__uuid
    
    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        elem = etree.SubElement(body, self.tag)
        elem.attrib["uuid"] = self.uuid()
        return root
    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        if elem is None:
            raise MessageParserError("could not find 'BookingRequest' element")
        uuid     = elem.attrib["uuid"]
        return cls(uuid)
    from_xml = classmethod(from_xml)
MessageBuilder.register(BookingRequest)

class AuctionBidResponse(BaseServerMessage):
    """Response to a ping request.
    <AuctionBid/>
    """
    tag = XBE("AuctionBid")
    
    def __init__(self, uuid, xbedurl, ticket, task_id, price):
        BaseServerMessage.__init__(self)
        self.__uuid    = uuid
        self.__xbedurl = xbedurl
        self.__ticket  = ticket
        self.__task_id = task_id
        self.__price   = price

    def uuid(self):
        return self.__uuid
    def xbedurl(self):
        return self.__xbedurl
    def ticket(self):
        return self.__ticket
    def task_id(self):
        return self.__task_id
    def price(self):
        return self.__price
    
    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        elem = etree.SubElement(body, self.tag)
        elem.attrib["uuid"]    = self.uuid()
        elem.attrib["xbedurl"] = self.xbedurl()
        elem.attrib["task-id"] = self.task_id()
        reservation = etree.SubElement(elem, XBE("Reservation"))
        etree.SubElement(reservation, XBE("Ticket")).text = self.ticket()
        price = etree.SubElement(elem, XBE("Price"))
        etree.SubElement(price, XBE("Cost")).text = str(self.price())

        return root
    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        if elem is None:
            raise MessageParserError("could not find 'AuctionBid' element")
        uuid     = elem.attrib["uuid"]
        xbedurl  = elem.attrib["xbedurl"]
        task_id  = elem.attrib.get("task-id")
        ticket   = elem.findtext(XBE("Reservation/Ticket"))
        if ticket is None:
            raise MessageParserError("no 'Ticket' found!")
        price   = float(elem.findtext(XBE("Price/Cost")))
        #price   = elem.findtext(XBE("Price/Cost"))
        if price is None:
            raise MessageParserError("no 'Price' found!")
        return cls(uuid, xbedurl, ticket, task_id, price)
    from_xml = classmethod(from_xml)
MessageBuilder.register(AuctionBidResponse)

class AuctionAccept(BaseServerMessage):
    """Response to a ping request.
    <AuctionAccept/>
    """
    tag = XBE("AuctionAccept")
    
    def __init__(self, uuid, ticket):
        BaseServerMessage.__init__(self)
        self.__uuid  = uuid
        self.__ticket = ticket

    def uuid(self):
        return self.__uuid
    def ticket(self):
        return self.__ticket

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        elem = etree.SubElement(body, self.tag)
        elem.attrib["uuid"] = self.uuid()
        reservation = etree.SubElement(elem, XBE("Reservation"))
        etree.SubElement(reservation, XBE("Ticket")).text = self.ticket()
        return root
    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        if elem is None:
            raise MessageParserError("could not find 'AuctionAccept' element")
        uuid     = elem.attrib["uuid"]
        ticket = elem.findtext(XBE("Reservation/Ticket"))
        if ticket is None:
            raise MessageParserError("no 'Ticket' found!")
        return cls(uuid, ticket)
    from_xml = classmethod(from_xml)
MessageBuilder.register(AuctionAccept)

class AuctionDeny(BaseServerMessage):
    """Response to a ping request.
    <AuctionDeny/>
    """
    tag = XBE("AuctionDeny")
    
    def __init__(self, uuid, ticket):
        BaseServerMessage.__init__(self)
        self.__uuid  = uuid
        self.__ticket = ticket

    def uuid(self):
        return self.__uuid
    def ticket(self):
        return self.__ticket

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        elem = etree.SubElement(body, self.tag)
        elem.attrib["uuid"] = self.uuid()
        reservation = etree.SubElement(elem, XBE("Reservation"))
        etree.SubElement(reservation, XBE("Ticket")).text = self.ticket()
        return root
    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        if elem is None:
            raise MessageParserError("could not find 'AuctionDeny' element")
        uuid     = elem.attrib["uuid"]
        ticket = elem.findtext(XBE("Reservation/Ticket"))
        if ticket is None:
            raise MessageParserError("no 'Ticket' found!")
        return cls(uuid, ticket)
    from_xml = classmethod(from_xml)
MessageBuilder.register(AuctionDeny)

class BookedResponse(BaseServerMessage):
    """Response to a ping request.
    <BookedResponse/>
    """
    tag = XBE("BookedResponse")
    
    def __init__(self, uuid, xbedid, xbedurl, ticket, task_id):
        BaseServerMessage.__init__(self)
        self.__uuid    = uuid
        self.__xbedid  = xbedid
        self.__xbedurl = xbedurl
        self.__ticket  = ticket
        self.__task_id = task_id

    def uuid(self):
        return self.__uuid
    def xbedid(self):
        return self.__xbedid
    def xbedurl(self):
        return self.__xbedurl
    def task_id(self):
        return self.__task_id
    def ticket(self):
        return self.__ticket
    
    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
        elem = etree.SubElement(body, self.tag)
        elem.attrib["uuid"]    = self.uuid()
        elem.attrib["xbedid"]  = self.xbedid()
        elem.attrib["xbedurl"] = self.xbedurl()
        elem.attrib["task-id"] = str(self.task_id())
        reservation = etree.SubElement(elem, XBE("Booked"))
        etree.SubElement(reservation, XBE("Ticket")).text = self.ticket()
        return root
    def from_xml(cls, root, hdr, body):
        elem = body.find(cls.tag)
        if elem is None:
            raise MessageParserError("could not find 'BookedResponse' element")
        uuid    = elem.attrib["uuid"]
        xbedid  = elem.attrib["xbedid"]
        xbedurl = elem.attrib["xbedurl"]
        task_id = elem.attrib.get("task-id")
        ticket  = elem.findtext(XBE("Booked/Ticket"))
        if ticket is None:
            raise MessageParserError("no 'Ticket' found!")
        return cls(uuid, xbedid, xbedurl, ticket, task_id)
    from_xml = classmethod(from_xml)
MessageBuilder.register(BookedResponse)

class BrokerError(Error):
    ns  = XBE
    tag = ns("BrokerError")
    
    def __init__(self, uuid, code=errcode.OK, msg=None):
        Error.__init__(self, code, msg)
        self.__uuid  = uuid

    def uuid(self):
        return self.__uuid

    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
	error = etree.SubElement(body, self.tag)
        
        error.attrib["uuid"] = self.uuid()
        error.attrib["code"] = str(self.code())
	etree.SubElement(error, self.ns("Name")).text = self.name()
        etree.SubElement(error, self.ns("Description")).text = self.description()
        if self.message() is not None:
            etree.SubElement(error, self.ns("Message")).text = self.message()
        return root

    def from_xml(cls, root, hdr, body):
        error = body.find(cls.tag)
        uuid  = error.attrib["uuid"]
        code = int(error.attrib["code"])
        msg = error.findtext(cls.ns("Message"))
        return cls(uuid, code, msg)
    from_xml = classmethod(from_xml)
MessageBuilder.register(BrokerError)        

class JobState(BaseServerMessage):
    ns  = XBE
    tag = ns("JobState")
    
    #def __init__(self, ticket, task_id, statecode=errcode.OK, msg=None):
    def __init__(self, ticket, task_id, state, msg=None):
        #Error.__init__(self, code, msg)
        BaseServerMessage.__init__(self)
        self.__ticket  = ticket
        self.__task_id = task_id
        self.__state   = state
        self.__msg     = msg
        
    def ticket(self):
        return self.__ticket
    def task_id(self):
        return self.__task_id
    def state(self):
        return self.__state
    def message(self):
        return self.__msg
    
    def as_xml(self):
        root, hdr, body = MessageBuilder.xml_parts()
	error = etree.SubElement(body, self.tag)

        error.attrib["task-id"] = self.task_id()
        
        error.attrib["ticket"] = self.ticket()
        error.attrib["state"] = str(self.state())

        reservation = etree.SubElement(error, XBE("Reservation"))
        etree.SubElement(reservation, XBE("Ticket")).text = self.ticket()

	#etree.SubElement(error, self.ns("Name")).text = self.name()
        #etree.SubElement(error, self.ns("Description")).text = self.description()
        if self.message() is not None:
            etree.SubElement(error, self.ns("Message")).text = self.message()
        return root

    def from_xml(cls, root, hdr, body):
        error = body.find(cls.tag)
        task_id  = error.attrib["task-id"]
        #state    = int(error.attrib["state"])
        state    = error.attrib["state"]
        msg      = error.findtext(cls.ns("Message"))

        ticket = error.findtext(XBE("Reservation/Ticket"))
        if ticket is None:
            raise MessageParserError("no 'Ticket' found!")
        return cls(ticket, task_id, state, msg)
    from_xml = classmethod(from_xml)
MessageBuilder.register(JobState)

#!/usr/bin/env python
"""
The Xen Based Execution Environment protocol
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

import logging, re, time, threading
log = logging.getLogger(__name__)

from pprint import pprint, pformat
from lxml import etree
from twisted.python import failure

from xbe.proto import XenBEEProtocolFactory, XenBEEProtocol
from xbe.xml.namespaces import *
from xbe.xml import xsdl, message, protocol, errcode, jsdl

from xbe.xbed.daemon import XBEDaemon
from xbe.xbed.ticketstore import TicketStore
from xbe.xbed.task import TaskManager
from xbe.xbed.instance import InstanceManager
            
class XenBEEClientProtocol(protocol.XMLProtocol):
    """The XBE client side protocol.

    This protocol is spoken between some client (user, script
    etc.). The protocol is based on XML
    """

    def __init__(self, client):
        protocol.XMLProtocol.__init__(self)
        self.client = client

    def connectionMade(self):
        log.debug("client %s has connected" % (self.client))
    
    def do_ConfirmReservation(self, elem, *args, **kw):
        try:
            confirm = message.MessageBuilder.from_xml(elem.getroottree())
        except Exception, e:
            return message.Error(errcode.ILLEGAL_REQUEST, str(e))
        log.debug("got confirmation with ticket %s" % confirm.ticket())
        ticket = TicketStore.getInstance().lookup(confirm.ticket())
        if ticket is None:
            return message.Error(errcode.TICKET_INVALID, confirm.ticket())
        
        xbed = XBEDaemon.getInstance()
        jsdl_doc = jsdl.JsdlDocument(schema_map=xbed.schema_map)
        parsed_jsdl = jsdl_doc.parse(confirm.jsdl())

        try:
            # does the job have our InstanceDescription element?
            # otherwise drop the job
            jsdl_doc.lookup_path(
                "JobDefinition/JobDescription/Resources/"+
                "InstanceDefinition/InstanceDescription")
        except Exception, e:
            TaskManager.getInstance().removeTask(ticket.task)
            del ticket.task
            TicketStore.getInstance().release(ticket)
            msg = message.Error(errcode.NO_INSTANCE_DESCRIPTION, str(e))
        else:
            ticket.task.confirm(confirm.jsdl(), jsdl_doc)
            if confirm.start_task():
                ticket.task.start()
            msg = None
        return msg

    def do_ReservationRequest(self, dom_node, *args, **kw):
        ticket = TicketStore.getInstance().new()
        if ticket is None:
            # if no ticket could be generated:
            msg = message.Error(errcode.SERVER_BUSY)
        else:
            task = TaskManager.getInstance().new()
            ticket.task = task
            msg = message.ReservationResponse(ticket.id(), task.id())
        return msg

    def do_CancelReservation(self, elem, *args, **kw):
        msg = message.MessageBuilder.from_xml(elem.getroottree())
        ticket = TicketStore.getInstance().lookup(msg.ticket())
        ticket.task.terminate("UserCancel")
        del ticket.task
        TicketStore.getInstance().release(ticket)

    def do_StartRequest(self, elem, *a, **kw):
        msg = message.MessageBuilder(elem.getroottree())
        ticket = TicketStore.getInstance().lookup(msg.ticket())
        ticket.task.start()

    def do_StatusRequest(self, elem, *args, **kw):
	"""Handle status request."""
        request = message.MessageBuilder.from_xml(elem.getroottree())
        task_id = request.task_id()
        status_list = message.StatusList()
        if task_id is not None:
            task = TaskManager.getInstance().lookupByID(task_id)
            if task is not None:
                status_list.add(task.id(), task.submitTime(), task.state())
            else:
                return message.Error(errcode.TASK_LOOKUP_FAILURE, task_id)
        else:
            for task in TaskManager.getInstance().tasks.values():
                status_list.add(task.id(), task.submitTime(), task.state())
        return status_list

    def do_Kill(self, elem, *args, **kw):
        kill = message.MessageBuilder.from_xml(elem.getroottree())
        task = self.factory.taskManager.lookupByID(kill.task_id())
        if not task:
            return message.Error(errcode.TASK_LOOKUP_FAILURE,
                                 "no such task: %s" % (tid,),)

    def do_ListCache(self, elem, *args, **kw):
        log.debug("retrieving cache list...")
        def __buildMessage(entries):
            msg = message.CacheEntries()
            for uid, uri, hash, type, desc in entries:
                logical_uri = "cache://xbe-file-cache/%s" % (str(uid))
                msg.add(logical_uri, hash, type, desc)
            return msg
        self.factory.cache.getEntries(
            ).addCallback(__buildMessage).addBoth(
            self.transformResultToMessage).addCallback(self.sendMessage)
        return None

	
class XenBEEInstanceProtocol(protocol.XMLProtocol):
    """The XBE instance side protocol.

    This protocol is spoken between an instance and the daemon.
    """

    def __init__(self, instid):
        protocol.XMLProtocol.__init__(self)
	self.instid = instid

    def executeTask(self, jsdl, task):
        msg = message.ExecuteTask(jsdl, task.id())
        self.task_id = task.id()
        self.sendMessage(msg.as_xml())

    def queryStatus(self):
        pass

    #########################
    #                       #
    # Message handling part #
    #                       #
    #########################
    def do_InstanceAvailable(self, xml, *args, **kw):
        inst_avail = message.MessageBuilder.from_xml(xml.getroottree())
        inst_id = inst_avail.inst_id()

        inst = InstanceManager.getInstance().lookupByUUID(inst_id)
        if inst is not None:
            inst.available(inst_avail, self)
        else:
            return message.Error(errcode.INSTANCE_LOOKUP_FAILURE)

    def do_ExecutionFinished(self, xml, *args, **kw):
        msg = message.MessageBuilder.from_xml(xml.getroottree())
        inst_id = msg.inst_id()
        exitcode = msg.exitcode()
        inst = InstanceManager.getInstance().lookupByUUID(inst_id)
        if inst is not None:
            inst.task.cb_execution_finished(exitcode)
        else:
            return message.Error(errcode.INSTANCE_LOOKUP_FAILURE)

    def do_InstanceAlive(self, xml, *a, **kw):
        msg = message.MessageBuilder.from_xml(xml.getroottree())
        inst = InstanceManager.getInstance().lookupByUUID(msg.inst_id())
        if inst is not None:
            inst.alive()
        else:
            return message.Error(errcode.INSTANCE_LOOKUP_FAILURE)

    def do_ExecutionFailed(self, xml, *a, **kw):
        msg = message.MessageBuilder.from_xml(xml.getroottree())
        inst = InstanceManager.getInstance().lookupByUUID(inst_id)
        if inst is not None:
            inst.task.failed(failure.Failure(msg))
        else:
            return message.Error(errcode.INSTANCE_LOOKUP_FAILURE)

    def do_InstanceShuttingDown(self, xml, *a, **kw):
        msg = message.MessageBuilder.from_xml(xml.getroottree())
        inst = InstanceManager.getInstance().lookupByUUID(inst_id)
        if inst is not None:
            log.info("instance is shutting down...")
        else:
            return message.Error(errcode.INSTANCE_LOOKUP_FAILURE)

class _XBEDProtocol(XenBEEProtocol):
    def post_connect(self):
        pass

class XenBEEDaemonProtocolFactory(XenBEEProtocolFactory):
    protocol = _XBEDProtocol
    
    def __init__(self, daemon, queue, topic, user, passwrd):
	XenBEEProtocolFactory.__init__(self, queue, user, passwrd)
        self.daemon = daemon
        self.__topic = topic
        self.__protocolRemovalTimeout = 60
        self.__clientProtocols = {}
        self.__clientMutex = threading.RLock()
        
        self.__instanceProtocols = {}
        self.__instanceMutex = threading.RLock()

	self.instanceManager = daemon.instanceManager
        self.taskManager = daemon.taskManager
        self.cache = daemon.cache
        self.cert = daemon.certificate
        self.ca_cert = daemon.ca_certificate

        from twisted.internet import task
        self.__cleanupLoop = task.LoopingCall(self.__cleanupOldProtocols)
        self.__cleanupLoop.start(5*60)

    def stompConnectionMade(self, stomp_prot):
        stomp_prot.subscribe(self.__topic)

    def dispatchToProtocol(self, transport, msg, domain, sourceType, sourceId=None):
        assert sourceType != None, "the source-type must not be None"
        
        if domain != "xenbee":
            raise ValueError("illegal domain: %s, expected 'xenbee'" % domain)
        if sourceId is None:
            raise ValueError(
                "illegal reply-to value, must be of the form: "+
                "/(queue|topic)/xenbee.[type].[id]")
        getattr(self, (sourceType.lower()+"Message"))(transport, msg, sourceId)

    def __messageHelper(self, id, msg, trnsprt, protocols, mtx, cls, *args, **kw):
        try:
            mtx.acquire()
            p = protocols.get(id)
            if p is None:
                p = cls(*args, **kw)
                p.factory = self
                protocols[id] = p
                p.makeConnection(trnsprt)
            p.timeOflastReceive = time.time()
        finally:
            mtx.release()
        log.debug("got message for %r" % (p,))
        d = p.messageReceived(msg)

        # log sent answers
        d.addCallback(self.logCallback,
                      log.debug, "sending answer to %(client)s: %(result)s",
                      {"client": id})
        
        # finally log any error and consume them
        d.addErrback(self.logCallback,
                     log.error,
                     "sending message %(message)s to %(client)s failed: %(result)s",
                     { "client":id, "message": str(msg)})

    def logCallback(self, result, logfunc, fmt, dictionary, *args, **kw):
        if result is not None:
            dictionary["result"] = result
            logfunc(fmt, dictionary, *args, **kw)
            
    def clientMessage(self, transport, msg, client):
        self.__messageHelper(client, msg, transport,
                             self.__clientProtocols,
                             self.__clientMutex,
                             protocol.SecureProtocol,
                             self.cert,
                             self.ca_cert,
                             self.certificateChecker,
                             XenBEEClientProtocol, client)

    def instanceMessage(self, transport, msg, inst):
        self.__messageHelper(inst, msg, transport,
                             self.__instanceProtocols,
                             self.__instanceMutex,
                             XenBEEInstanceProtocol, inst)

    def certificateChecker(self, certificate):
        return XBEDaemon.getInstance().userDatabase.check_x509(certificate)

    # clean up registered protocols after some inactivity threshold
    def __cleanupOldProtocols(self):
        self.__cleanupHelper(self.__clientProtocols, self.__clientMutex)
        self.__cleanupHelper(self.__instanceProtocols, self.__instanceMutex)

    def __cleanupHelper(self, protocols, mtx):
        try:
            mtx.acquire()
            tbr = [] # list of 'to be removed' items
            for id, p in protocols.iteritems():
                if (p.timeOflastReceive + self.__protocolRemovalTimeout) < time.time():
                    log.debug(
                        "removing registered protocol %s due to inactivity." % (id,))
                    tbr.append(id)
            map(protocols.pop, tbr)
        finally:
            mtx.release()

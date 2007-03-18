#!/usr/bin/env python
"""
The Xen Based Execution Environment protocol
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

# system imports
import logging, re, time, threading
log = logging.getLogger(__name__)

from pprint import pprint, pformat
from lxml import etree

# twisted imports
from twisted.python import failure
from twisted.internet import defer

# XBE imports
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
        ticket = TicketStore.getInstance().lookup(confirm.ticket())
        if ticket is None:
            return message.Error(errcode.TICKET_INVALID, confirm.ticket())
        log.debug("got confirmation with ticket %s" % confirm.ticket())
        
        xbed = XBEDaemon.getInstance()
        jsdl_doc = jsdl.JsdlDocument(schema_map=xbed.schema_map)
        try:
            etree.clearErrorLog()
            parsed_jsdl = jsdl_doc.parse(confirm.jsdl())
        except etree.DocumentInvalid, e:
            log.info("got invalid document: %s" % str(e.error_log))
            TaskManager.getInstance().removeTask(ticket.task)
            del ticket.task
            TicketStore.getInstance().release(ticket)
            return message.Error(errcode.ILLEGAL_REQUEST, "JSDL document is invalid: %s" % (e.error_log,))

        try:
            # does the job have our InstanceDescription element?
            # otherwise drop the job
            jsdl_doc.lookup_path(
                "JobDefinition/JobDescription/Resources/"+
                "InstanceDefinition/InstanceDescription")
        except Exception, e:
            TicketStore.getInstance().release(ticket)
            TaskManager.getInstance().removeTask(ticket.task)
            del ticket.task
            msg = message.Error(errcode.NO_INSTANCE_DESCRIPTION, str(e))
        else:
            ticket.task.confirm(confirm.jsdl(), jsdl_doc)
            if confirm.start_task():
                ticket.task.start()
            msg = message.Error(errcode.OK, "reservation confirmed")
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
        return self.do_TerminateRequest(elem, *args, **kw)

    def do_TerminateRequest(self, elem, *args, **kw):
        msg = message.MessageBuilder.from_xml(elem.getroottree())
        log.debug(str(msg.ticket()))
        ticket = TicketStore.getInstance().lookup(msg.ticket())
        if ticket is not None:
            if not ticket.task.is_done():
                TaskManager.getInstance().terminateTask(ticket.task, "UserCancel")
                return message.Error(errcode.OK, "termination in progress")
        else:
            return message.Error(errcode.TICKET_INVALID, msg.ticket())

    def do_StartRequest(self, elem, *a, **kw):
        msg = message.MessageBuilder(elem.getroottree())
        ticket = TicketStore.getInstance().lookup(msg.ticket())
        if ticket is not None:
            ticket.task.start()
        else:
            return message.Error(errcode.TICKET_INVALID, msg.ticket())

    def do_StatusRequest(self, elem, *args, **kw):
	"""Handle status request."""
        request = message.MessageBuilder.from_xml(elem.getroottree())
        ticket = TicketStore.getInstance().lookup(request.ticket())
        status_list = message.StatusList()
        try:
            if ticket is not None:
                task = ticket.task
                status_list.add(task.id(), task.state(), task.getStatusInfo())
                
                # remove the task entry
                if task.is_done() and request.removeEntry():
                    log.debug("removing task-entry: %s", task.id())
                    TaskManager.getInstance().removeTask(task)
                    TicketStore.getInstance().release(ticket)
                    del ticket.task
            elif request.ticket() == "all":
                log.info("user requested the status of all tasks, remove that functionality")
                for task in TaskManager.getInstance().tasks.values():
                    status_list.add(task.id(), task.state(), task.getStatusInfo())
            else:
                return message.Error(errcode.TICKET_INVALID, request.ticket())
            return status_list
        except Exception, e:
            self.log.warn("status request failed %s", e, exc_info=1)

    def do_ListCache(self, elem, *args, **kw):
        log.debug("retrieving cache list...")
        def __buildMessage(entries):
            msg = message.CacheEntries()
            for uid, uri, hash, type, desc in entries:
                logical_uri = "cache://xbe-file-cache/%s" % (str(uid))
                meta = {
                    "hash": hash,
                    "type": type,
                    "description": desc,
                }
                msg.add(logical_uri, meta)
            return msg
        self.factory.cache.getEntries(
            ).addCallback(__buildMessage).addBoth(
            self.transformResultToMessage).addCallback(self.sendMessage)
        return None

    def do_CacheFile(self, elem, *a, **kw):
        msg = message.MessageBuilder.from_xml(elem.getroottree())
        log.debug("caching file: %s", msg.uri())
        cached = XBEDaemon.getInstance().cache
        d = cached.cache(msg.uri(), msg.type_of_file(), msg.description())

        def _success(uid):
            return message.Error(errcode.OK, uid)
        def _failure(reason):
            return message.Error(errcode.CACHING_FAILED, reason.getErrorMessage())
        d.addCallback(_success).addErrback(_failure).addCallback(self.sendMessage)
	
class XenBEEInstanceProtocol(protocol.XMLProtocol):
    """The XBE instance side protocol.

    This protocol is spoken between an instance and the daemon.
    """

    def __init__(self, instid):
        protocol.XMLProtocol.__init__(self)
	self.instid = instid

    def executeTask(self, jsdl, task):
        """send the request to the application.

        return a Deferred, that gets called when the task has finished.
        """
        msg = message.ExecuteTask(jsdl, task.id())
        self.task_id = task.id()
        self.sendMessage(msg.as_xml())

    def queryStatus(self):
        # TODO: implement
        raise NotImplementedError("queryStatus is not yet implemented")

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
            inst.available(self)
        else:
            log.warn("got available message from suspicious source")

    def do_ExecutionFinished(self, xml, *args, **kw):
        msg = message.MessageBuilder.from_xml(xml.getroottree())
        inst_id = msg.inst_id()
        exitcode = msg.exitcode()
        inst = InstanceManager.getInstance().lookupByUUID(inst_id)
        if inst is not None:
            log.debug("execution on instance %s finished" % inst_id)
            try:
                inst.task.signalExecutionEnd(exitcode)
            except Exception, e:
                log.warn("could not signal execution end: %s" % e)
        else:
            log.warn("got execution finished from suspicious source")

    def do_InstanceAlive(self, xml, *a, **kw):
        msg = message.MessageBuilder.from_xml(xml.getroottree())
        inst_id = msg.inst_id()
        inst = InstanceManager.getInstance().lookupByUUID(msg.inst_id())
        if inst is not None:
            inst.update_alive()
        else:
            log.warn("got alive message from suspicious source")
            
    def do_ExecutionFailed(self, xml, *a, **kw):
        msg = message.MessageBuilder.from_xml(xml.getroottree())
        inst_id = msg.inst_id()
        inst = InstanceManager.getInstance().lookupByUUID(inst_id)
        if inst is not None:
            log.debug("execution on instance %s failed: %s" % (inst_id, msg.reason()))
            try:
                inst.task.signalExecutionFailed(Exception("execution failed", msg))
            except Exception, e:
                log.warn("could not signal execution failure: %s" % e)
        else:
            log.warn("got ExecutionFailed message from suspicious source")

    def do_InstanceShuttingDown(self, xml, *a, **kw):
        msg = message.MessageBuilder.from_xml(xml.getroottree())
        inst_id = msg.inst_id()
        inst = InstanceManager.getInstance().lookupByUUID(inst_id)
        if inst is not None:
            log.info("instance is shutting down...")
            log.debug("execution on instance %s finished" % inst_id)
            try:
                inst.task.signalExecutionEnd(0)
            except Exception, e:
                log.warn("could not signal execution end: %s" % e)
        else:
            log.warn("got execution finished from suspicious source")

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
#        log.debug("got message for %r" % (p,))
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

    def logCallback(self, result, logfunc, fmt, dictionary):
        if result is not None:
            dictionary["result"] = str(result)
            logfunc(fmt % dictionary)
            
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

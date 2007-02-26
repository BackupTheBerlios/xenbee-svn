#!/usr/bin/env python
"""
The Xen Based Execution Environment protocol
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

import logging, re, time, threading
log = logging.getLogger(__name__)

from pprint import pprint, pformat
from xbe.proto import XenBEEProtocolFactory, XenBEEProtocol
from lxml import etree
from xbe.xml.security import X509SecurityLayer, X509Certificate, SecurityError
from xbe.xml.namespaces import *
from xbe.xml import xsdl, message, protocol, errcode, jsdl

from xbe.xbed.daemon import XBEDaemon
from xbe.xbed.ticketstore import TicketStore
from xbe.xbed.task import TaskManager
            
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
        print "handling request:", request.as_str()
        status_list = message.StatusList()
        if task_id is not None:
            task = TaskManager.getInstance().lookupByID(task_id)
            if task is not None:
                status_list.add(task.id(), task.submitTime(), task.state())
            else:
                return message.Error(errcode.TASK_LOOKUP_FAILURE, task_id)
        else:
            pprint(TaskManager.getInstance().tasks)
            for task in TaskManager.getInstance().tasks.values():
                print "adding task", task.id()
                status_list.add(task.id(), task.submitTime(), task.state())
        print status_list.as_str()
        return status_list

    def do_Kill(self, elem, *args, **kw):
        kill = message.MessageBuilder.from_xml(elem.getroottree())
        task = self.factory.taskManager.lookupByID(kill.task_id())
        if not task:
            return message.Error(errcode.TASK_LOOKUP_FAILURE,
                                 "no such task: %s" % (tid,),)
        task.kill(kill.signal())
#        sig = int(elem.findtext(xsdl.XSDL("Signal")))
#        if not sig in [ 9, 15 ]:
#            return xsdl.XenBEEError("Signal out of range, allowed are (9,15)",
#                                    xsdl.ErrorCode.SIGNAL_OUT_OF_RANGE)
#        tid = elem.find(xsdl.XSDL("JobID"))
#        task = self.factory.taskManager.lookupByID(tid)
#        task.kill(sig)
#        return xsdl.XenBEEError("signal sent", xsdl.ErrorCode.OK)

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

    def __init__(self, instid, transport):
        protocol.XMLProtocol.__init__(self, transport)
	self.instid = instid
        self.addUnderstood(XSDL("InstanceAvailable"))
        self.addUnderstood(XSDL("TaskStatusNotification"))

    def executeTask(self, task):
        if task.document.tag != JSDL("JobDefinition"):
            job = task.document.find(JSDL("JobDefinition"))
        else:
            job = task.document
        if job is None:
            raise RuntimeError("no job definition found for task %s" % (task.id()))
        msg = xsdl.XenBEEClientMessage()
        msg.root.append(etree.fromstring(etree.tostring(job)))

        log.info("submitting:\n%s" % str(msg))
        self.transport.write(msg.to_s())

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

        if inst_id != self.instid:
            raise ValueError("got answer from different instance!")

        inst = self.factory.instanceManager.lookupByUUID(inst_id)
        if not inst:
            return message.Error(errcode.INSTANCE_LOOKUP_FAILURE)
        if inst.task == None:
            raise ValueError("no task belongs to this instance")
        inst.protocol = self
        inst.available(inst_avail)

    def do_TaskFinished(self, status, *args, **kw):
        fin_elem = status.find(XSDL("TaskFinished"))
        exitcode = int(fin_elem.findtext(XSDL("ExitCode")))
        stdout = fin_elem.findtext(XSDL("StandardOutput"))
        errout = fin_elem.findtext(XSDL("ErrorOutput"))
        log.info("task finished:\ncode=%d\nstdout='%s'\nerrout='%s'" % (exitcode, stdout, errout))

        task = self.factory.instanceManager.lookupByUUID(self.instid).task
        task.status_elem = status
        task.finished(exitcode)

class _XBEDProtocol(XenBEEProtocol):
    def post_connect(self):
        pass

class XenBEEDaemonProtocolFactory(XenBEEProtocolFactory):
    protocol = _XBEDProtocol
    
    def __init__(self, daemon, queue):
	XenBEEProtocolFactory.__init__(self, queue, "daemon", "test1234")
        self.daemon = daemon
        self.__protocolRemovalTimeout = 60
        self.__clientProtocols = {}
        self.__clientMutex = threading.RLock()
        
        self.__instanceProtocols = {}
        self.__instanceMutex = threading.RLock()

	self.instanceManager = daemon.instanceManager
        self.taskManager = daemon.taskManager
        self.cache = daemon.cache
        self.portal = daemon.portal
        self.cert = daemon.certificate
        self.ca_cert = daemon.ca_certificate

        from twisted.internet import task
        self.__cleanupLoop = task.LoopingCall(self.__cleanupOldProtocols)
        self.__cleanupLoop.start(10)

    def dispatchToProtocol(self, transport, msg, domain, sourceType, sourceId=None):
        assert sourceType != None, "the source-type must not be None"
        
        if domain != "xenbee":
            raise ValueError("illegal domain: %s, expected 'xenbee'" % domain)
        if sourceId is None:
            raise ValueError(
                "illegal reply-to value, must be of the form: /(queue|topic)/xenbee.[type].[id]")
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
                     log.error, "sending message %(message)s to %(client)s failed: %(result)s",
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
                             XenBEEClientProtocol, client)

    def instanceMessage(self, transport, msg, inst):
        self.__messageHelper(inst, msg, transport,
                             self.__instanceProtocols,
                             self.__instanceMutex,
                             XenBEEInstanceProtocol, inst)


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
                    log.debug("removing registered protocol %s due to inactivity." % (id,))
                    tbr.append(id)
            map(protocols.pop, tbr)
        finally:
            mtx.release()

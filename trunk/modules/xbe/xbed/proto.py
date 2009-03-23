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
from twisted.internet import defer, reactor, threads

# XBE imports
from xbe.proto import XenBEEProtocolFactory, XenBEEProtocol
from xbe.xml.namespaces import *
from xbe.xml import xsdl, message, protocol, errcode, jsdl
from xbe.concurrency import LockMgr

from xbe.xbed.daemon import XBEDaemon
from xbe.xbed.ticketstore import TicketStore
from xbe.xbed.task import TaskManager
from xbe.xbed.instance import InstanceManager

import xbe.xbed.xbemsg_pb2 as xbemsg

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
#            TaskManager.getInstance().removeTask(ticket.task)
#            del ticket.task
#            TicketStore.getInstance().release(ticket)
            return message.Error(errcode.ILLEGAL_REQUEST, "JSDL document is invalid: %s" % (e.error_log,))

        try:
            # does the job have our InstanceDescription element?
            # otherwise drop the job
            jsdl_doc.lookup_path(
                "JobDefinition/JobDescription/Resources/"+
                "InstanceDefinition/InstanceDescription")
        except Exception, e:
#            TicketStore.getInstance().release(ticket)
#            TaskManager.getInstance().removeTask(ticket.task)
#            del ticket.task
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
            task = TaskManager.getInstance().new(ticket.id())
            ticket.task = task
            msg = message.ReservationResponse(ticket.id(), task.id())
        return msg

    def do_TerminateRequest(self, elem, *args, **kw):
        msg = message.MessageBuilder.from_xml(elem.getroottree())
        log.debug(str(msg.ticket()))
        ticket = TicketStore.getInstance().lookup(msg.ticket())
        if ticket is not None:
            if not ticket.task.is_done():
                reactor.callInThread(TaskManager.getInstance().terminateTask, ticket.task, msg.reason())
                return message.Error(errcode.OK, "termination in progress")
        else:
            return message.Error(errcode.TICKET_INVALID, msg.ticket())

    def do_StartRequest(self, elem, *a, **kw):
        msg = message.MessageBuilder(elem.getroottree())
        ticket = TicketStore.getInstance().lookup(msg.ticket())
        if ticket is not None:
            reactor.callInThread(ticket.task.start)
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
                status_list.add(task.id(), task.state(), ticket.id(), task.getStatusInfo())

                # remove the task entry
                if task.is_done() and request.removeEntry():
                    log.debug("removing task-entry: %s", task.id())
                    TaskManager.getInstance().removeTask(task)
                    TicketStore.getInstance().release(ticket)
                    del ticket.task
            elif request.ticket() == "all":
                log.info("user requested the status of all tasks, remove that functionality")
                toberemoved = [] 
		for tid, ticket in TicketStore.getInstance().all().iteritems():
                    if ticket.task:
                        task = ticket.task
                        status_list.add(task.id(), task.state(), ticket.id(), task.getStatusInfo())

	                # remove the task entry
	                if task.is_done() and request.removeEntry():
                            toberemoved.append( (ticket, task) )
                for (ticket, task) in toberemoved:
                    log.debug("removing task-entry: %s", task.id())
                    TaskManager.getInstance().removeTask(task)
                    TicketStore.getInstance().release(ticket)
                    del ticket.task
            else:
                return message.Error(errcode.TICKET_INVALID, request.ticket())
            return status_list
        except Exception, e:
            log.warn("status request failed %s", e, exc_info=1)

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

    def do_CacheRemove(self, elem, *a, **kw):
        msg = message.MessageBuilder.from_xml(elem.getroottree())
        log.debug("removing cache entry: %s", msg.uri())
        cached = XBEDaemon.getInstance().cache
        d = cached.remove(msg.uri())

        def _success(uid):
            return message.Error(errcode.OK, uid)
        def _failure(reason):
            return message.Error(errcode.INTERNAL_SERVER_ERROR, reason.getErrorMessage())
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

    def requestStatus(self, caller, executeStatusTask=False):
        caller.signalStatus("n/a")

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

class BaseProtocol(object):
    def __init__(self):
        self.mtx = threading.RLock()
        self.factory = None
        self.connected = 0
        self.transport = None

    def makeConnection(self, transport):
        self.connected = 1
        self.transport = transport
        self.connectionMade()

    def connectionMade(self):
        pass
    def connectionLost(self):
        pass

    def messageReceived(self, msg):
        pass
    def requestStatus(self, caller, executeStatusTask=False):
        pass
    def executeTask(self, caller, jsdl):
        pass
    def requestTermination(self, caller, reason=None):
        pass
    def requestShutdown(self, caller, reason=None):
        pass
    
    def sendMessage(self, msg):
        l = LockMgr(self.mtx)
        if msg is not None:
            if self.connected and self.transport:
                try:
                    self.transport.write(msg)
                except Exception, e:
                    log.error("message `%s' could not be sent: %s" % (str(msg), str(e)))
            else:
                log.warn("tried to send a message while not connected!")

class XenBEEInstanceProtocolPB(BaseProtocol):
    def __init__(self, instanceID):
        BaseProtocol.__init__(self)
        self._instanceID = instanceID
        self._conv_id = None
        self._task_id = 0
        self.log = logging.getLogger("xbed.proto.instance.%s" % instanceID)
        self.log.debug("initializing protocol")

    def connectionMade(self):
        BaseProtocol.connectionMade(self)
        self.log.debug("connection made")
    
    def connectionLost(self):
        self.log.debug("connection lost")
        BaseProtocol.connectionLost(self)

    def messageReceived(self, msg):
        m = xbemsg.XbeMessage()
        reply = None
        try:
            m.ParseFromString(msg)
            if not m.IsInitialized():
                raise ValueError("could not parse message into XbeMessage: unknown reason")
            self.log.debug("received message: %s" % m)

            conv_id = m.header.conversation_id
            if self._conv_id is None:
                self._conv_id = conv_id
            if self._conv_id != conv_id:
                raise RuntimeError("wrong conversation-id: got: %s, expected: %s" % (conv_id, self._conv_id))

            if m.HasField("error"):
                reply = self.do_error(m.error)
            elif m.HasField("execute"):
                reply = self.do_execute(m.execute)
            elif m.HasField("execute_ack"):
                reply = self.do_execute_ack(m.execute_ack)
            elif m.HasField("execute_nak"):
                reply = self.do_execute_nak(m.execute_nak)
            elif m.HasField("status_req"):
                reply = self.do_status_req(m.status_req)
            elif m.HasField("status"):
                reply = self.do_status(m.status)
            elif m.HasField("finished"):
                reply = self.do_finished(m.finished)
            elif m.HasField("finished_ack"):
                reply = self.do_finished_ack(m.finished_ack)
            elif m.HasField("failed"):
                reply = self.do_failed(m.failed)
            elif m.HasField("failed_ack"):
                reply = self.do_failed_ack(m.failed_ack)
            elif m.HasField("shutdown"):
                reply = self.do_shutdown(m.shutdown)
            elif m.HasField("shutdown_ack"):
                reply = self.do_shutdown_ack(m.shutdown_ack)
            elif m.HasField("terminate"):
                reply = self.do_terminate(m.terminate)
            elif m.HasField("terminate_ack"):
                reply = self.do_terminate_ack(m.terminate_ack)
            elif m.HasField("life_sign"):
                reply = self.do_life_sign(m.life_sign)
            else:
                raise RuntimeError("message does not contain any element")
        except Exception, e:
            self.log.error("received message could not be handled: %s", e)

        if reply is not None:
            self.log.debug("replying with: %s", reply)
            self.sendMessage(reply.SerializeToString())

    def requestStatus(self, caller, executeStatusTask=False):
        self.log.info("requesting status from instance")
        msg = xbemsg.XbeMessage()
        msg.header.conversation_id = self._conv_id
        msg.status_req.execute_status_task = executeStatusTask
        self.sendMessage(msg.SerializeToString())

    def executeTask(self, caller, jsdl):
        #TODO: translate jsdl to PB
        msg = xbemsg.XbeMessage()
        msg.header.conversation_id = self._conv_id
        msg.execute.main_task.executable = "/bin/sleep"
        msg.execute.main_task.argument.append("600")
        e = msg.execute.main_task.env.add()
        e.key = "HOME"
        e.val = "/"
        msg.execute.main_task.wd = "/"
        msg.execute.status_task.executable = "/bin/ps"
        msg.execute.status_task.argument.append("aux")
        
        self.log.info("sending request for execution to instance: %s", msg)
        self.sendMessage(msg.SerializeToString())

    def requestTermination(self, caller, reason=None):
        self.log.info("sending request for termination to instance")
        msg = xbemsg.XbeMessage()
        msg.header.conversation_id = self._conv_id
        msg.terminate.task = self._task_id
        self.sendMessage(msg.SerializeToString())

    def requestShutdown(self, caller, reason=None):
        self.log.info("sending request for shutdown to instance")
        msg = xbemsg.XbeMessage()
        msg.header.conversation_id = self._conv_id
        msg.shutdown.reason = str(reason)
        self.sendMessage(msg.SerializeToString())

    def do_error(self, error):
        self.log.info("instance had an error: %s", error)

    def do_execute(self, execute):
        pass

    def do_execute_ack(self, execute_ack):
        self.log.info("execution accepted by instance: %s", execute_ack)
        self._task_id = execute_ack.task

    def do_execute_nak(self, execute_nak):
        self.log.info("execution *not* accepted by instance: %s", execute_nak)

    def do_status_req(self, status_req):
        pass

    def do_status(self, status):
        self.log.info("received status information: %s", status)

        inst = InstanceManager.getInstance().lookupByUUID(self._instanceID)
        if inst is not None:
            inst.task.signalStatus(status)

    def do_finished(self, finished):
        self.log.info("execution on instance has finished: %d", finished.exitcode)
        # send a finished ack to the instance
        ack = xbemsg.XbeMessage()
        ack.header.conversation_id = self._conv_id
        ack.finished_ack.task = finished.task
        
        inst = InstanceManager.getInstance().lookupByUUID(self._instanceID)
        if inst is not None:
            inst.task.signalExecutionEnd(finished.exitcode)

        return ack

    def do_finished_ack(self, finished_ack):
        pass

    def do_failed(self, failed):
        self.log.info("execution on instance has failed: %d", failed.reason)
        # send a failed ack to the instance
        ack = xbemsg.XbeMessage()
        ack.header.conversation_id = self._conv_id
        ack.failed_ack.task = failed.task

        inst = InstanceManager.getInstance().lookupByUUID(self._instanceID)
        if inst is not None:
            inst.task.signalExecutionFailed(failed.reason)
        return ack

    def do_failed_ack(self, failed_ack):
        pass

    def do_shutdown(self, shutdown):
        pass

    def do_shutdown_ack(self, shutdown_ack):
        self.log.info("instance acknowledged shutdown request")

    def do_terminate(self, terminate):
        pass

    def do_terminate_ack(self, terminate_ack):
        self.log.info("instance acknowledged terminate request")

    def do_life_sign(self, life_sign):
        self.log.debug("instance %s is alive", self._instanceID)
        inst = InstanceManager.getInstance().lookupByUUID(self._instanceID)
        if inst is not None:
            inst.life_sign(self, life_sign)
        else:
            self.log.warn("unknown instance: %s", self._instanceID)
            self.requestShutdown(None, None)

class _XBEDProtocol(XenBEEProtocol):
    def post_connect(self):
        pass

class XenBEEDaemonProtocolFactory(XenBEEProtocolFactory):
    protocol = _XBEDProtocol

    def __init__(self, daemon, queue, topic, user, password):
	XenBEEProtocolFactory.__init__(self, queue, user, password)
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
        if d is not None:
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
#         self.__messageHelper(inst, msg, transport,
#                              self.__instanceProtocols,
#                              self.__instanceMutex,
#                              XenBEEInstanceProtocolPB, inst)
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

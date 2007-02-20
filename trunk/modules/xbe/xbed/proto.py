#!/usr/bin/env python
"""
The Xen Based Execution Environment protocol
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

import logging, re, time, threading
log = logging.getLogger(__name__)

from xbe.proto import XenBEEProtocolFactory, XenBEEProtocol
from lxml import etree
from xbe.xml.security import X509SecurityLayer, X509Certificate, SecurityError
from xbe.xml.namespaces import *
from xbe.xml import xsdl, message, protocol, errcode
            
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
    
    def do_JobDefinition(self, job, *args, **kw):
        log.debug("got new job")

        # does the job have our InstanceDefinition element?
        # otherwise drop the job
        if not job.find(XSDL("InstanceDefinition")):
            return message.Error(errcode.ILLEGAL_REQUEST,
                                 "no InstanceDefinition found.")
        # we should be able to handle the job
        task = self.factory.taskManager.newTask(job)
        return message.Error(errcode.OK,
                             "task submitted: %s" % task.ID())

    def do_StatusRequest(self, dom_node, *args, **kw):
	"""Handle status request."""
        status_list = message.StatusList()
        map(status_list.add, self.factory.taskManager.tasks.values())
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
            raise RuntimeError("no job definition found for task %s" % (task.ID()))
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
    
    def __init__(self, daemon, queue="/queue/xenbee.daemon"):
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

#!/usr/bin/env python
"""
The Xen Based Execution Environment protocol
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

import logging, re, time, threading
log = logging.getLogger(__name__)

from xbe.xml import xsdl
from xbe.proto import XenBEEProtocolFactory, XenBEEProtocol
from lxml import etree

class XenBEEClientProtocol(xsdl.XMLProtocol):
    """The XBE client side protocol.

    This protocol is spoken between some client (user, script
    etc.). The protocol is based on XML
    """

    def __init__(self, client, transport):
        xsdl.XMLProtocol.__init__(self, transport)
        self.client = client
        self.addUnderstood(xsdl.Tag("ImageSubmission"))
        self.addUnderstood(xsdl.Tag("StatusRequest"))
        self.addUnderstood(xsdl.Tag("Kill"))
        self.addUnderstood(xsdl.Tag("ListCache"))
        self.addUnderstood(xsdl.Tag("JobDefinition", xsdl.JSDL_NS))

    def do_JobDefinition(self, job):
        log.debug("got new job")

        # does the job have our InstanceDefinition element?
        # otherwise drop the job
        if not job.find(xsdl.XSDL("InstanceDefinition")):
            return xsdl.XenBEEError("no InstanceDefinition found.",
                                    xsdl.ErrorCode.ILLEGAL_REQUEST)

        # we should be able to handle the job
        task = self.factory.taskManager.newTask(job)
        return xsdl.XenBEEError("task submitted: %s" % task.ID(),
                                xsdl.ErrorCode.OK)

    def do_StatusRequest(self, dom_node):
	"""Handle status request."""
        msg = xsdl.XenBEEStatusMessage()
        map(msg.addStatusForTask, self.factory.taskManager.tasks.values())
        return msg

    def do_Kill(self, elem):
        sig = int(elem.findtext(xsdl.XSDL("Signal")))
        if not sig in [ 9, 15 ]:
            return xsdl.XenBEEError("Signal out of range, allowed are (9,15)",
                                    xsdl.ErrorCode.SIGNAL_OUT_OF_RANGE)
        tid = elem.find(xsdl.XSDL("JobID"))
        task = self.factory.taskManager.lookupByID(tid)
        if not task:
            return xsdl.XenBEEError("no such task: %s" % (tid,),
                                    xsdl.ErrorCode.TASK_LOOKUP_FAILURE)
        task.kill(sig)
        return xsdl.XenBEEError("signal sent", xsdl.ErrorCode.OK)

    def do_ListCache(self, elem):
        def __buildMessage(entries):
            msg = xsdl.XenBEECacheEntries()
            for uid, type, desc in entries:
                msg.addEntry(uid, type, desc)
            return msg
        return self.factory.cache.getEntries().addCallback(__buildMessage)
	
class XenBEEInstanceProtocol(xsdl.XMLProtocol):
    """The XBE instance side protocol.

    This protocol is spoken between an instance and the daemon.
    """

    def __init__(self, instid, transport):
        xsdl.XMLProtocol.__init__(self, transport)
	self.instid = instid
        self.addUnderstood(xsdl.Tag("InstanceAvailable"))
        self.addUnderstood(xsdl.Tag("TaskStatusNotification"))

    def executeTask(self, task):
        if task.document.tag != xsdl.Tag("JobDefinition", xsdl.JSDL_NS):
            job = task.document.find(xsdl.JSDL("JobDefinition"))
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
    def do_InstanceAvailable(self, inst_avail):
        inst_id = inst_avail.findtext(xsdl.XSDL("InstanceID"))
        if inst_id != self.instid:
            raise ValueError("got answer from different instance!")

        inst = self.factory.instanceManager.lookupByUUID(inst_id)
        if not inst:
            return xsdl.XenBEEError("no such instance",
                                    xsdl.ErrorCode.INSTANCE_LOOKUP_FAILURE)
        if inst.task == None:
            raise ValueError("no task belongs to this instance")

        # retrieve network information
        fqdn = inst_avail.findtext(xsdl.XSDL("NodeInformation/Network/FQDN"))
        ips = [ ip.text for ip in inst_avail.findall(xsdl.XSDL("NodeInformation/Network/IPList/IP")) ]
        log.debug("instance %s available at %s [%s]" % (inst_id, fqdn, ",".join(ips)))

        inst.protocol = self
        inst.available(fqdn, ips)

    def do_TaskStatusNotification(self, status):
        fin_elem = status.find(xsdl.XSDL("TaskFinished"))
        exitcode = int(fin_elem.findtext(xsdl.XSDL("ExitCode")))
        stdout = fin_elem.findtext(xsdl.XSDL("StandardOutput"))
        errout = fin_elem.findtext(xsdl.XSDL("ErrorOutput"))
        log.info("task finished:\ncode=%d\nstdout='%s'\nerrout='%s'" % (exitcode, stdout, errout))

        task = self.factory.instanceManager.lookupByUUID(self.instid).task
        task.status_elem = status_elem
        task.finished(exitcode)

class _XBEDProtocol(XenBEEProtocol):
    def post_connect(self):
        pass

class XenBEEDaemonProtocolFactory(XenBEEProtocolFactory):
    protocol = _XBEDProtocol
    
    def __init__(self, daemon, queue="/queue/xenbee.daemon"):
	XenBEEProtocolFactory.__init__(self, daemon, queue)

        self.__protocolRemovalTimeout = 60
        self.__clientProtocols = {}
        self.__clientMutex = threading.RLock()
        
        self.__instanceProtocols = {}
        self.__instanceMutex = threading.RLock()

	self.instanceManager = daemon.instanceManager
        self.taskManager = daemon.taskManager
        self.cache = daemon.cache

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

    def __messageHelper(self, id, msg, trnsprt, protocols, mtx, cls):
        try:
            mtx.acquire()
            p = protocols.get(id)
            if p is None:
                p = cls(id, trnsprt)
                p.factory = self
                protocols[id] = p
            p.timeOflastReceive = time.time()
        finally:
            mtx.release()
        d = p.messageReceived(msg)

        # log sent answers
        d.addCallback(str)
        d.addCallback(self.logCallback,
                      log.debug, "sending answer to %(client)s: %(result)s",
                      {"client": id})
        
        # finally log any error and consume them
        d.addErrback(self.logCallback,
                     log.error, "sending message %(message)s to %(client)s failed: %(result)s",
                     { "client":id, "message": str(msg)})

    def logCallback(self, result, logfunc, fmt, dictionary, *args, **kw):
        dictionary["result"] = result
        logfunc(fmt, dictionary, *args, **kw)
            
    def clientMessage(self, transport, msg, client):
        self.__messageHelper(client, msg, transport,
                             self.__clientProtocols,
                             self.__clientMutex,
                             XenBEEClientProtocol)

    def instanceMessage(self, transport, msg, inst):
        self.__messageHelper(inst, msg, transport,
                             self.__instanceProtocols,
                             self.__instanceMutex,
                             XenBEEInstanceProtocol)


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

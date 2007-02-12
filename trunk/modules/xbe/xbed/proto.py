#!/usr/bin/env python
"""
The Xen Based Execution Environment protocol
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

import logging, re
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
            raise ValueError("no InstanceDefinition found.")

        # we should be able to handle the job
        task = self.factory.taskManager.newTask(job)
        self.transport.write(
            str(xsdl.XenBEEClientError("task submitted: %s" % task.ID(),
                                       xsdl.XenBEEClientError.OK))
            )

    def do_ImageSubmission(self, elem):
	"""Handle an image submission."""
        # run some checks on the received document
	imgDef = elem.find(xsdl.XSDL("ImageDefinition"))
	if not imgDef:
	    raise Exception("no ImageDefinition found.")

        # create a new task object for this submission
        task = self.factory.taskManager.newTask(elem)
        self.transport.write(
            str(xsdl.XenBEEClientError("task submitted: %s" % task.ID(),
                                       xsdl.XenBEEClientError.OK))
            )

    def do_StatusRequest(self, dom_node):
	"""Handle status request."""
        msg = xsdl.XenBEEStatusMessage()
        map(msg.addStatusForTask, self.factory.taskManager.tasks.values())
        self.transport.write(str(msg))

    def do_Kill(self, elem):
        sig = int(elem.findtext(xsdl.XSDL("Signal")))
        if not sig in [ 9, 15 ]:
            raise ValueError("out of range, allowed are (9,15)")
        for tid in map(lambda t: (t.text or "").strip(), elem.findall(xsdl.XSDL("JobID"))):
            task = self.factory.taskManager.lookupByID(tid)
            if not task:
                self.transport.write(            
                    str(xsdl.XenBEEClientError("no such task: %s" % (tid,),
                                               xsdl.XenBEEClientError.ILLEGAL_REQUEST))
                    )
            else:
                task.kill(sig)
        self.transport.write(
            str(xsdl.XenBEEClientError("signal sent", xsdl.XenBEEClientError.OK)))

    def do_ListCache(self, elem):
        def __sendMessage(entries):
            msg = xsdl.XenBEECacheEntries()
            for uid, type, desc in entries:
                msg.addEntry(uid, type, desc)
            self.transport.write(str(msg))
        self.factory.cache.getEntries().addCallback(__sendMessage)
	
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
        self.transport.write(str(msg))

    def queryStatus(self):
        pass

    #########################
    #                       #
    # Message handling part #
    #                       #
    #########################
    def do_InstanceAvailable(self, dom_node):
        inst_id = xsdl.getChild(dom_node, "InstanceID").text.strip()
        if inst_id != self.instid:
            raise ValueError("got answer from different instance!")
        inst = self.factory.instanceManager.lookupByUUID(inst_id)
        if not inst:
            raise ValueError("no such instance")
        if inst.task == None:
            raise ValueError("no task belongs to this instance")
        inst.protocol = self
        inst.available()

    def do_TaskStatusNotification(self, status_elem):
        fin_elem = xsdl.getChild(status_elem, "TaskFinished")
        exitcode = int(xsdl.getChild(fin_elem, "ExitCode").text)
        errout   = xsdl.getChild(fin_elem, "ErrorOutput").text
        log.info("task finished: code=%d errout='%s'" % (exitcode, errout))

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

	self.instanceManager = daemon.instanceManager
        self.taskManager = daemon.taskManager
        self.cache = daemon.cache

    def dispatchToProtocol(self, transport, msg, domain, sourceType, sourceId=None):
        if domain != "xenbee":
            raise ValueError("illegal domain: %s, expected 'xenbee'" % domain)
        if sourceId is None:
            raise ValueError(
                "illegal reply-to value, must be of the form: /(queue|topic)/xenbee.[type].[id]")
        getattr(self, "new"+sourceType.capitalize())(transport, msg, sourceId)

    def newClient(self, transport, msg, client):
        log.debug("new client connected: %s" % client)
	clientProtocol = XenBEEClientProtocol(client, transport)
	clientProtocol.factory = self
        clientProtocol.messageReceived(msg)

    def newInstance(self, transport, msg, inst):
        log.debug("new instance connected: %s" % inst)
        instProtocol = XenBEEInstanceProtocol(inst, transport)
	instProtocol.factory = self
        instProtocol.messageReceived(msg)

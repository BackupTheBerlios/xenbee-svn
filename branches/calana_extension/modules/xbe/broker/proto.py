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

__version__ = "$Rev: 458 $"
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
from xbe.stomp.proto import StompTransport
from xbe.proto import XenBEEProtocolFactory, XenBEEProtocol
from xbe.xml.namespaces import *
from xbe.xml import xsdl, message, protocol, errcode, jsdl
####from xbe.xml import message, errcode, protocol as xmlprotocol, jsdl
from xbe.concurrency import LockMgr
from xbe.util.uuid import uuid

from twisted.internet import task
from xbe.broker.daemon import CalanaBrokerDaemon

from xbe.broker import BrokerDispatcher_sm
from xbe.broker import job

##################################################
##
##################################################
class Reply:
    def __init__(self):
        self.hasMsg = False
        self.msg = None

        
class CommandFailed(Exception):
    pass

##################################################
##
##################################################
class XenBEEClient2BrokerProtocol(protocol.XMLProtocol):
#class XenBEEClient2BrokerProtocol(protocol.SecureProtocol):
    """The XBE client side protocol.

    This protocol is spoken between some client (user, script
    etc.). The protocol is based on XML
    """

    def __init__(self, client):
        protocol.XMLProtocol.__init__(self)
        #protocol.XMLProtocol.__init__(self)
        self.mtx    = threading.RLock()
        self.client = client
        self.__job  = job.Job(self.factory)
        
        # smc State Machine
        self.__fsm = BrokerDispatcher_sm.BrokerDispatcher_sm(self)
        self.__fsm.setDebugFlag(2)

        self.__pollCounter = 0
        self.__xbedaemonTimer = {}
        self.__auctionBids = {}
        self.__nextTransition = "PollReq"

        self.__hasBids  = False
        self.__hasPongs = False
        self.__requestend = 0
        self.__xbedid   = 0
        self.__xbeproto = 0

        self.__hasProviderError    = False
        self.__statusProvider      = 0

        self.triggerFSM = task.LoopingCall(self.handleFSM)


    def handleFSM(self):
        log.debug("XenBEEClient2BrokerProtocol::handleFSM event '%s'", self.__nextTransition)
        #self.incrPollCounter()
        #if (self.getPollCounter()> 5):
        #    self.triggerFSM.stop()

    

    def getJob(self):
        if self.hasBids():
            return self.factory.jobGet(self.bid().ticket())
        else:
            return self.__job
        
    def connectionMade(self):
        log.debug("=====+++ client %s has connected" % (self.client))
        #layer = self.getsecurityLayer()
        cl = self.factory.getClient(self.client)
        if hasattr(cl, "cert"):
            subject = cl.cert().subject()
            self.__job.setUser(subject)
            log.debug("Have CERT '%s'" % subject)
        else:
            log.debug("DO NOT Have CERT")
        self.triggerFSM.start(1, now=False)

    def recvResponse(self, xbedaemon, what, response):
        xbed = xbedaemon.xbedaemon
        log.debug("===***=== recvPesponse -> %s '%s'" %( what, xbed))
        #getattr(self, (what+"Message"))(transport, msg, sourceId)
        if hasattr(self, ("do_recv"+what)):
            getattr(self, ("do_recv"+what))(xbedaemon, response)
        else:
            log.info("Command not found : '%s'" % what)
            #            raise CommandFailed("No such Transition '%s'." % self.__nextTransition)
            
    def do_recvPong(self, xbed, pong):
        log.debug("===***=== do_recvPong")
        if self.hasPongs():
            log.debug("===***=== do_recvPong have it")
            pass
        else:
            log.debug("===***=== do_recvPong -> pong is new, save it")
            self.__hasPongs  = True
            self.__xbedid    = xbed.xbedaemon
            self.__xbedproto = xbed
            self.__auctionBids[self.__xbedid] = pong
        
    def do_recvBid(self, xbed, bid):
        log.debug("===***=== do_recvBid")
        log.debug("===Price %3.2f" % bid.price())
        if self.hasBids():
            # return AuctionDeny
            log.debug("===***=== do_recvBid have it -> reject the this one")
            self.factory.sendAuctionDeny(xbed, bid.uuid(), bid.ticket(), bid.task_id())
        else:
            log.debug("===***=== do_recvBid -> bid is new, save it")
            self.__hasBids  = True
            self.__xbedid    = xbed.xbedaemon
            self.__xbedproto = xbed
            self.__auctionBids[self.__xbedid] = bid
            self.__job.setBid(bid)
            self.factory.jobAdd(bid.ticket(), self.__job)
            self.__job = None
         
    def do_recvBrokerError(self, xbed, response):
        log.debug("===***=== do_recvBrokerError '%s'" % response)
        self.__hasProviderError    = True
        self.__statusProvider      = response


    #
    def messageBooked(self):
        bid = self.__auctionBids[self.__xbedid]
        return message.BookedResponse(bid.uuid(), self.__xbedid, bid.xbedurl(), bid.ticket(), bid.task_id())

    #
    def sendAuctionAccept(self, response):
        self.__pollCounter = 0
        bid = self.__auctionBids[self.__xbedid]
        self.factory.sendAuctionAccept(self.__xbedproto, bid.uuid(), bid.ticket(), bid.task_id())

    def sendConfirmReservation(self, response):
        self.__pollCounter = 0
        self.factory.sendConfirmReservation(self.__xbedproto, response)

    #
    def do_PollRequest(self, elem, *args, **kw):
        log.debug("XenBEEClient2BrokerProtocol::do_PollRequest()")
        log.debug("Current: '%s'" % self.__fsm.getState().getName())
        request = message.MessageBuilder.from_xml(elem.getroottree())
        log.debug("XenBEEClient2BrokerProtocol::do_PollRequest() %s",
                  request.cmd_name())
        event = self.__nextTransition
        if event is None:
            event = "PollReq"
        if hasattr(self.__fsm, event):
            log.debug("========== Next ===>  %s, p=%d"
                      % (event, self.getPollCounter()))

        reply = Reply()
        try:
            while reply.hasMsg == False:
                event = self.popEvent()
                if event is None:
                    event = "PollReq"
                if hasattr(self.__fsm, event):
                    getattr(self.__fsm, event)(self.getJob(), self, request, reply)
                else:
                    raise CommandFailed("No such Transition '%s'." % self.__nextTransition)

            log.debug("XenBEEClient2BrokerProtocol::do_PollRequest() has message '%s'"% reply.msg)
            return reply.msg
        except Exception, e:
            msg = message.Error(errcode.ILLEGAL_REQUEST,
                                "PollReq failed: Transition failed in State '%s'. '%s'" %
                                (self.__fsm.getState().getName() , e))

        return msg


    def do_PingRequest(self, elem, *args, **kw):
        log.debug("XenBEEClient2BrokerProtocol::do_PingRequest()")
        log.debug("Current: '%s'" % self.__fsm.getState().getName())
        request = message.MessageBuilder.from_xml(elem.getroottree())
        reply = Reply()
        try:
            self.__fsm.PingReq(self.getJob(), self, reply)
            msg = reply.msg
        except Exception, e:
            msg = message.Error(errcode.ILLEGAL_REQUEST,
                                "PingRequest failed: Transition failed in State '%s': '%s'" % 
                                (self.__fsm.getState().getName() , e))
            log.debug("XenBEEClient2BrokerProtocol::do_PingRequest() FAIL")

        log.debug("do_PingRequest: '%s'" % msg)
        return msg

    def do_BookingRequest(self, elem, *args, **kw):
        msg = message.MessageBuilder.from_xml(elem.getroottree())
        log.debug("bookingRequest: ")
        reply = Reply()
        try:
            self.__fsm.BookingReq(self.getJob(), self, reply)
            msg = reply.msg
        except Exception, e:
            msg = message.Error(errcode.ILLEGAL_REQUEST,
                                "BookingRequest failed: Transition failed State '%s': '%s'" %
                                (self.__fsm.getState().getName() , e))
            log.debug("XenBEEClient2BrokerProtocol::do_BookingRequest() FAIL")
            
        log.debug("response (%s)" % msg)
        return msg
            
    def do_ConfirmReservation(self, elem, *args, **kw):
        log.debug("=============== XenBEEClient2BrokerProtocol::do_ConfirmReservation")
        msgin = message.MessageBuilder.from_xml(elem.getroottree())
        log.debug("bookingRequest: ")
        reply = Reply()
        try:
            self.__fsm.Confirm(self.getJob(), self, msgin, reply)
            msg = reply.msg
        except Exception, e:
            msg = message.Error(errcode.ILLEGAL_REQUEST,
                                "BookingRequest failed: Transition failed State '%s': '%s'" %
                                (self.__fsm.getState().getName() , e))
            log.debug("XenBEEClient2BrokerProtocol::do_BookingRequest() FAIL")
            
        log.debug("response (%s)" % msg)
        return msg

    def _success(uid):
        return message.Error(errcode.OK, uid)
    def _failure(reason):
        return message.Error(errcode.INTERNAL_SERVER_ERROR, reason.getErrorMessage())

    #
    #
    def pushEvent(self, event):
        self.__nextTransition = event
        
    def popEvent(self):
        if self.__nextTransition is None:
            return None #event = "PollReq"
        else:
            event = self.__nextTransition
            self.__nextTransition = None
        return event

    def getPollCounter(self):
        return self.__pollCounter
    
    def incrPollCounter(self):
        self.__pollCounter = self.__pollCounter+1

    def clearXBEDaemon(self):
        for id, p in self.__xbedaemonTimer.iteritems():
            p = 0

    def addXBEDaemon(self, id):
        self.__xbedaemonTimer[id] = time.time()

    #
    def bid(self):
        return self.__auctionBids[self.__xbedid]

    def hasBids(self):
        return self.__hasBids
    
    def hasPongs(self):
        return self.__hasPongs

    def hasProviderError(self):
        return self.__hasProviderError
    
    def clearProviderError(self):
        self.__hasProviderError    = False
        self.__statusProvider      = 0

    def getProviderErrorCode(self):
        return self.__statusProvider.code()

    def hasResponses(self):
        return self.hasBids() or self.hasPongs()
    
    def ReqLen(self):
        return len(self.__xbedaemonTimer)

    def RespLen(self):
        return len(self.__auctionBids)

            
    # Define StateMachine Actions here
    # wait for Pong from xenbee Daemon
    def waitForResponse(self, job, reqCtxt, request, reply):
        # e.g. can handle timer
        reply.hasMsg = True
        reply.msg = message.PollResponse(self.client, request.cmd_name())
        log.debug("=== *** XenBEEBrokerProtocolFactory::waitForResponse '%s' " % request.cmd_name())
        
        reqCtxt.incrPollCounter()
        if (self.__requestend < time.time()):
            reqCtxt.pushEvent("EndReq")
        else:
            reqCtxt.pushEvent("PollReq")

    def waitForAck(self, job, reqCtxt, request, reply):
        log.debug("XenBEEBrokerProtocolFactory::waitForAck")
        reply.hasMsg = True
        reply.msg = message.PollResponse(self.client, request.cmd_name())
        log.debug("=== *** XenBEEBrokerProtocolFactory::waitForResponse '%s' " % request.cmd_name())
        
        reqCtxt.incrPollCounter()
        if reqCtxt.getPollCounter() > 2:
            reqCtxt.pushEvent("ProviderRejected")
        else:
            if reqCtxt.hasProviderError():
                # evaluate result
                if reqCtxt.getProviderErrorCode():
                    reqCtxt.pushEvent("ProviderBooked")
                else:
                    reqCtxt.pushEvent("ProviderRejected")
                reqCtxt.clearProviderError()
            else:
                reqCtxt.pushEvent("PollReq")
        
    def waitForConfirm(self, job, reqCtxt, request, reply):
        log.debug("XenBEEBrokerProtocolFactory::waitForConfirm")
        reply.hasMsg = True
        reply.msg = message.PollResponse(self.client, request.cmd_name())
        log.debug("=== *** XenBEEBrokerProtocolFactory::waitForResponse '%s' " % request.cmd_name())
        
        reqCtxt.incrPollCounter()
        if reqCtxt.getPollCounter() > 2:
            reqCtxt.pushEvent("ProviderClose")
        else:
            if reqCtxt.hasProviderError():
                # evaluate result
                if reqCtxt.getProviderErrorCode():
                    reqCtxt.pushEvent("ProviderClose")
                else:
                    reqCtxt.pushEvent("ProviderClose")
                reqCtxt.clearProviderError()
            else:
                reqCtxt.pushEvent("PollReq")

    # brokerCtxt   has type BrokerRequestContext
    # job          has type 
    # bid          has type 
    def inBookingReq(self, job, reqCtxt, reply):
        log.debug("XenBEEBrokerProtocolFactory::inBookingReq")
        self.clearXBEDaemon()
        self.__hasBids    = False
        self.__requestend = reqCtxt.daemon.factory.bid_timeout + time.time()
        reply.hasMsg = True

        try:
            self.factory.sendBookingRequest(MyData)
            job.nextEvent(MyData)
            reply.msg = message.PollResponse(self.client, "BookedResponse")
            log.debug("========== Sendet %d bookingRequest" % MyData.ReqLen())
        except Exception, e:
            job.terminate(MyData)
            log.debug("inBookingReq Failed: '%s'" % e )
            reply.msg = message.Error(errcode.ILLEGAL_REQUEST, "No XbeDaemons connected. '%s'" % e)

    def endSuccessfulAuction(self, job, reqCtxt, bid, reply): ##job, brokerCtxt):
        # send do_Cancel to most of xbedaemons
        # do_ConfirmReservation
        log.debug("XenBEEBrokerProtocolFactory::endSuccessfulAuction")
        reqCtxt.sendAuctionAccept(bid)

    def endFailureAuction(self, job, reqCtxt, request, reply): ##job, brokerCtxt):
    #def endFailureAuction(self, job, brokerCtxt):
        log.debug("XenBEEBrokerProtocolFactory::endFailureAuction")
        reqCtxt.pushEvent("BookingRejectedAck")
        job.terminate(reqCtxt)

    def inProviderBooked(self, job, reqCtxt, request, reply):
        #def inProviderBooked(self, job, brokerCtxt):
        # send AuctionAccept to the first one,
        # send AuctionDeny to all others
        log.debug("XenBEEBrokerProtocolFactory::inProviderBooked")

        reply.hasMsg = True
        reply.msg = reqCtxt.messageBooked()
        job.do_Event("endNegotiation", reqCtxt)

    def inProviderBookingRejected(self, job, reqCtxt, request, reply):
        log.debug("XenBEEBrokerProtocolFactory::inProviderBookingRejected")
        reply.hasMsg = True
        reply.msg = message.Error(errcode.SERVER_BUSY)
        job.do_Event("terminate", reqCtxt)
        
    def inConfirm(self, job, reqCtxt, request, reply):
        log.debug("XenBEEBrokerProtocolFactory::inConfirm")
        reply.hasMsg = True
        try:
            reqCtxt.sendConfirmReservation(request)
            reply.msg = message.PollResponse(self.client, "ConfirmResponse")
        except Exception, e:
            log.debug("inConfirm Failed: '%s'" % e )
            reply.msg = message.Error(errcode.ILLEGAL_REQUEST, "No XbeDaemons connected. '%s'" % e)
        
        #confirm = message.MessageBuilder.from_xml(elem.getroottree())
        #return message.Error(errcode.ILLEGAL_REQUEST, str(e))
        #ticket = TicketStore.getInstance().lookup(confirm.ticket())
        #if ticket is None:
        #    return message.Error(errcode.TICKET_INVALID, confirm.ticket())
        #log.debug("got confirmation with ticket %s" % confirm.ticket())

    def inProviderClose(self, job, brokerCtxt, request, reply):
        log.debug("XenBEEBrokerProtocolFactory::")

    def outClose(self, job, brokerCtxt, request, reply):
        log.debug("XenBEEBrokerProtocolFactory::")

    def inCloseAck(self, job, brokerCtxt, request, reply):
        log.debug("XenBEEBrokerProtocolFactory::")

    def inBookingRejectedAck(self, job, reqCtxt, request, reply):
        reply.hasMsg = True
        #reply.msg = message.Error(errcode.ILLEGAL_REQUEST, "Ping failed")
        reply.msg = message.Error(errcode.SERVER_BUSY)

    # do the same for ping
    # send ping to all xenbeeDaemons
    def inPingReq(self, job, MyData, reply):
        log.debug("XenBEEBrokerProtocolFactory::inPingReq for %s" % MyData.client)
        self._hasPongs = False
        reply.hasMsg   = True
        self.clearXBEDaemon()
        try:
            self.factory.sendPingRequest(MyData)
            reply.msg = message.PollResponse(self.client, "PongResponse")
            log.debug("========== Sendet %d pingRequest" % MyData.ReqLen())
        except Exception, e:
            log.debug("inPingReq Failed: '%s'" % e )
            reply.msg = message.Error(errcode.ILLEGAL_REQUEST, "No XbeDaemons connected. '%s'" % e)
        
    # Have Pong, send pong to xbe Client
    def endFailurePing(self, job, reqCtxt, request, reply):
        log.debug("=== *** XenBEEBrokerProtocolFactory::endFailurePing")
        reqCtxt.pushEvent("BookingRejectedAck")

    # Have Pong, send pong to xbe Client
    def endSuccessfulPing(self, job, reqCtxt, request, reply):
        log.debug("=== *** XenBEEBrokerProtocolFactory::endSuccessfulPing")
        reply.hasMsg = True
        if hasattr(message, request.cmd_name()):
            reply.msg = getattr(message, request.cmd_name())("None", 1)
        else:
            reply.msg = message.Error(errcode.ILLEGAL_REQUEST, "No such command")

    
##################################################
##
##################################################
class XenBEEDaemon2BrokerProtocol(protocol.XMLProtocol):
    """The XBE instance side protocol.

    This protocol is spoken between an instance and the daemon.
    """

    def __init__(self, xbedaemon):
        protocol.XMLProtocol.__init__(self)
        self.xbedaemon = xbedaemon

    def connectionMade(self):
        log.debug("===== xbeDaemon %s has connected" % (self.xbedaemon))

    def makeConnection(self, transport):
        #self.connected = 1
        self.transport = transport
        #self.transport = xmlprotocol.XMLTransport(
        #        StompTransport(stomp_protocol, "/queue/xenbee.daemon.1"))
        log.debug("===== XenBEEDaemon2BrokerProtocol - makeConnection")
        #self.connectionMade()
        pass

    def sendPingRequest(self, clientProto):
	log.info("send a ping request to xbed '%s' with id '%s'" %
                 (self.xbedaemon , clientProto.client))
        msg = message.PingRequest(clientProto.client)

        #log.debug("sending: %s" % msg.as_xml())
        #log.debug("transport: %s" % self.transport)
        self.sendMessage(self.transformResultToMessage(msg))

    def sendBookingRequest(self, clientProto):
        msg = message.BookingRequest(clientProto.client)
        self.sendMessage(self.transformResultToMessage(msg))

    def sendAuctionAccept(self, uuid, ticket, task_id):
        msg = message.AuctionAccept(uuid, ticket)
        log.debug("sending: %s" % msg.as_xml())
        self.sendMessage(self.transformResultToMessage(msg))

    def sendAuctionDeny(self, uuid, ticket, task_id):
        msg = message.AuctionDeny(uuid, ticket)
        log.debug("sending: %s" % msg.as_xml())
        self.sendMessage(self.transformResultToMessage(msg))

    def sendConfirmReservation(self, msg):
        #msg = message.BookingRequest(clientProto.client)
        log.debug("====****====  sendConfirmReservation: sending: %s" % msg.as_xml())
        self.sendMessage(self.transformResultToMessage(msg))

    def do_EstablishMLS(self, xml, *args, **kw):
        log.debug("do_EstablishMLS: ")
        pass

    def do_XbedAvailable(self, xml, *args, **kw):
        msg = message.MessageBuilder.from_xml(xml.getroottree())
        log.debug("do_XbedAvailable: '%s'" % msg.as_xml())

    def do_XbedAlive(self, xml, *args, **kw):
        msg = message.MessageBuilder.from_xml(xml.getroottree())
        log.debug("do_XbedAlive: '%s'" % msg.as_xml())

    def do_PongResponse(self, elem, *a, **kw):
        pongMsg = message.MessageBuilder.from_xml(elem.getroottree()) 
        self.factory.propagateResponseToClient(pongMsg.uuid(), "Pong", self, pongMsg)

    def do_AuctionBid(self, elem, *a, **kw):
        auctionBidMsg = message.MessageBuilder.from_xml(elem.getroottree()) 
        log.debug("======= %s =====" % type(auctionBidMsg))
        self.factory.propagateResponseToClient(auctionBidMsg.uuid(), "Bid", self, auctionBidMsg)

    def do_ReservationConfirm(self, err, *args, **kw):
        log.debug("======================= do_ReservationConfirm: ")
        msg = message.MessageBuilder.from_xml(err.getroottree()) 
        self.factory.propagateResponseToJob(msg.ticket, "confirm", self, msg)
        self.factory.propagateResponseToClient(msg.uuid(), "Confirm", self, msg)

    def do_ConfirmAck(self, err, *args, **kw):
        log.debug("======================= do_ConfirmAck: ")
        msg = message.MessageBuilder.from_xml(err.getroottree()) 
        self.factory.propagateResponseToJob(msg.ticket(), "confirm", self, msg)
        #self.factory.propagateResponseToClient(msg.uuid(), "Confirm", self, msg)

    def do_JobState(self, err, *args, **kw):
        log.debug("======================= do_JobState: ")
        msg = message.MessageBuilder.from_xml(err.getroottree()) 
        log.debug("====>>%s, [%s], %s" % (msg.ticket(), msg.state(), msg.message()))
        self.factory.propagateResponseToJob(msg.ticket(), msg.state(), self, msg)
        
    def do_BrokerError(self, err, *args, **kw):
        log.debug("======================= do_BrokerError: ")
        errorMsg = message.MessageBuilder.from_xml(err.getroottree()) 
        self.factory.propagateResponseToClient(errorMsg.uuid(), "BrokerError", self, errorMsg)
    


##################################################
##
##################################################
class BaseProtocol(object):
    def __init__(self):
        self.mtx = threading.RLock()
        self.factory = None
        self.connected = 0
        self.transport = None

    def makeConnection(self, transport):
        self.connected = 1
        self.transport = transport
        log.debug("===== BaseProtocol:makeConnection")
        self.connectionMade()

    def connectionMade(self):
        log.debug("===== BaseProtocol::connectionMade")
        pass
    def connectionLost(self):
        pass
    
    def messageReceived(self, msg):
        log.debug("BaseProtocol:messageReceived")
        pass
    
##################################################
##
##################################################
    
##################################################
##
##################################################
class _XBEBrokerProtocol(XenBEEProtocol):
    def post_connect(self):
        pass

class XenBEEBrokerProtocolFactory(XenBEEProtocolFactory):
    protocol = _XBEBrokerProtocol

    def __init__(self, daemon, my_queue, topic, server_queue, user, password):
        log.debug("initializing broker protocol factory: id=%s,user=%s,server=%s" %
                  (my_queue, user, server_queue))

	XenBEEProtocolFactory.__init__(self, my_queue, user, password)
        self.daemon = daemon
        self.__topic = topic
        self.__server_queue = server_queue
        self.__protocolRemovalTimeout = 60
        self.__clientProtocols = {}
        self.__clientMutex = threading.RLock()

        self.__daemonProtocols = {}
        self.__daemonMutex = threading.RLock()

        self.cert = daemon.certificate
        self.ca_cert = daemon.ca_certificate

        self.__jobList = {}
        self.__jobMutex = threading.RLock()

        from twisted.internet import task
        self.__cleanupLoop = task.LoopingCall(self.__cleanupOldProtocols)
        self.__cleanupLoop.start(5*60)

    def jobAdd(self, ticket, job):
        log.debug("=====> Add Job....'%s'" % ticket)
        self.__jobList[ticket] = job
        pass

    def jobGet(self, ticket):
        p = self.__jobList.get(ticket)
        if p is None:
            log.debug("no job found found '%s' " % ticket)
            return None
        else:
            return p

    def jobEvent(self, ticket, event, reqCtxt):
        log.debug("jobEvent from '%s' to %s" % (event, ticket))
        p = self.__jobList.get(ticket)
        if p is None:
            log.debug("no job found found")
        else:
            log.debug("propagate event to job. " )
            p.do_EventByMap(event, reqCtxt)
    
    def propagateResponseToJob(self, ticket, event, reqCtxt, msg):
        self.jobEvent(ticket, event, reqCtxt)
        pass
    
    def sendPingRequest(self, clientProto):
        log.debug("=================== sendPingRequest")
        if len(self.__daemonProtocols) < 1:
            log.debug("no daemon found")
            raise CommandFailed("no daemon connected.")

        for id, p in self.__daemonProtocols.iteritems():
            p.sendPingRequest(clientProto)
            clientProto.addXBEDaemon(id)

    def sendBookingRequest(self, clientProto):
        log.debug("sendBookingRequest")
        if len(self.__daemonProtocols) < 1:
            log.debug("no daemon found")
            raise CommandFailed("no daemon connected.")
        for id, p in self.__daemonProtocols.iteritems():
            p.sendBookingRequest(clientProto)
            clientProto.addXBEDaemon(id)

    def sendAuctionAccept(self, xbed, uuid, ticket, task_id):
        log.debug("sendAuctionAccept uuid '%s'" % uuid)
        log.debug("sendAuctionAccept ticket '%s'" % ticket)
        xbed.sendAuctionAccept(uuid, ticket, task_id)

    def sendAuctionDeny(self, xbed, uuid, ticket, task_id):
        log.debug("sendAuctionDeny uuid '%s'" % uuid)
        log.debug("sendAuctionDeny ticket '%s'" % ticket)
        xbed.sendAuctionDeny(uuid, ticket, task_id)

    def sendConfirmReservation(self, xbed, msg):
        log.debug("====****==== Main::sendConfirmReservation")
        xbed.sendConfirmReservation(msg)

    def getClient(self, client):
        p = self.__clientProtocols.get(client)
        if p is None:
            log.debug("no client found")
            return None
        else:
            log.debug("propagate response to client. '%s'" % p.protocol)
            return p

    def propagateResponseToClient(self, client, event, xbedaemon, response):
        log.debug("propagateResponseResponseToClient from '%s' to %s" % (xbedaemon, client))
        p = self.__clientProtocols.get(client)
        if p is None:
            log.debug("no client found")
        else:
            log.debug("propagate response to client. '%s'" % p.protocol)
            p.protocol.recvResponse(xbedaemon, event, response)

    def propagateReservationConfirmToClient(self, client, xbedaemon, response):
        log.debug("propagateReservationConfirmToClient %s", client)
        p = self.__clientProtocols.get(client)
        if p is None:
            log.debug("no client found")
        else:
            log.debug("propagate AuctionBid to client. '%s'" % p.protocol)
            p.protocol.recvReservationConfirm(xbedaemon, response)

        
    #def propagateAuctionBidToClient(self, client, xbedaemon, response):
    #    log.debug("propagateAuctionBidToClient %s", client)
    #    p = self.__clientProtocols.get(client)
    #    if p is None:
    #        log.debug("no client found")
    #    else:
    #        log.debug("propagate AuctionBid to client. '%s'" % p.protocol)
    #        p.protocol.recvAuctionBid(xbedaemon, response)

    def stompConnectionMade(self, stomp_prot):
        log.debug("===== stompConnectionMade")
        stomp_prot.subscribe(self.__topic)

    def dispatchToProtocol(self, transport, msg, domain, sourceType, sourceId=None):
        assert sourceType != None, "the source-type must not be None"

        if domain != "xenbee":
            raise ValueError("illegal domain: %s, expected 'xenbee'" % domain)

        log.debug("dispatchToProtocol: %s" % transport)
        if sourceId is None:
            raise ValueError(
                "illegal reply-to value, must be of the form: "+
                "/(queue|topic)/xenbee.[type].[id]")
        getattr(self, (sourceType.lower()+"Message"))(transport, msg, sourceId)

    def errorReceived(self, error):
        log.debug("======================= errorReceived: ")
        pass

    def __messageHelper(self, id, msg, trnsprt, protocols, mtx, cls, *args, **kw):
        try:
            mtx.acquire()
            p = protocols.get(id)
            log.debug("__messageHelper: client/daemon '%s' not found p=%s." % (id, protocols))
            if p is None:
                p = cls(*args, **kw)
                p.factory = self
                protocols[id] = p
                p.makeConnection(trnsprt)
                p.timeOflastReceive = time.time()
            else:
                log.debug("__messageHelper: client/daemon '%s' FOUND found p=%s." % (id, protocols))
        finally:
            mtx.release()
            log.debug("got message for %r" % (p,))
            d = p.messageReceived(msg)
            log.debug("messageReceiver done")
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
                             XenBEEClient2BrokerProtocol, client)

    def daemonMessage(self, transport, msg, daemon):
        self.__messageHelper(daemon, msg, transport,
                             self.__daemonProtocols,
                             self.__daemonMutex,
                             XenBEEDaemon2BrokerProtocol, daemon)

    def certificateChecker(self, certificate):
        return CalanaBrokerDaemon.getInstance().userDatabase.check_x509(certificate)

    # clean up registered protocols after some inactivity threshold
    def __cleanupOldProtocols(self):
        self.__cleanupHelper(self.__clientProtocols, self.__clientMutex)
        #self.__cleanupHelper(self.__instanceProtocols, self.__instanceMutex)

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

        
class BrokerRequestContext():
    def __init__(self):
        log.debug("====== XenBEEBrokerProtocolFactory::BrokerRequestContext")
        
class Bid():
    def __init__(self):
        log.debug("====== XenBEEBrokerProtocolFactory::Bid")

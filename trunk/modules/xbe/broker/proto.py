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
import random
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

        
class BidContext:
    def __init__(self, bid, xbedproto):
        self.__bid = bid
        self.__xbedproto = xbedproto
    def bid(self):
        return self.__bid
    def xbedproto(self):
        return self.__xbedproto
    
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
        self.__jobList = {}
        
        # smc State Machine
        self.__fsm = BrokerDispatcher_sm.BrokerDispatcher_sm(self)
        self.__fsm.setDebugFlag(2)

        self.__xbedaemonTimer = {}
        self.__auctionBids = {}
        self.__nextTransition = ["PollReq"]

        self.__hasBestBid = False
        self.__hasBids    = False
        self.__hasPongs   = False
        self.__requestend = 0
        self.__xbedid     = 0
        self.__xbeproto   = 0

        self.__hasProviderError    = False
        self.__statusProvider      = 0
        self.__bestbid_ticket      = None

        self.__reply    = Reply()
        self.triggerFSM = task.LoopingCall(self.handleFSM)


    def getFSM(self):
        return self.__fsm

    def stopFSM(self):
        log.debug("Stopping FSM")
        self.triggerFSM.stop()

    def handleFSM(self):
        log.debug("XenBEEClient2BrokerProtocol::handleFSM client=%s eventstack='%s'" %
                  (self.client, self.__nextTransition))
        request = ""
        reply = Reply()
        try:
            event = self.popEvent()
            if event is None:
                return
            log.debug("===handleFSM event '%s'", event)
            if hasattr(self.__fsm, event):
                getattr(self.__fsm, event)(self.getJob(), self)
            else:
                raise CommandFailed("No such Transition '%s'." % self.__nextTransition)
        except Exception, e:
            log.debug("FSM Failed: transition failed in State '%s' : '%s'" %
                      (self.__fsm.getState().getName() , e))
            self.sendReply(self._failure("FSM Failed: transition failed in State '%s' : '%s'" %
                      (self.__fsm.getState().getName() , e)))
            self.stopFSM()
        pass

    def getJob(self):
        log.debug("Getjob: '%s'" % (self.__bestbid_ticket))
        if self.hasBestBid():
            job = self.factory.jobGet(self.__bestbid_ticket)
            log.debug("Got: '%s'" % job.ticket())
            return job
            #return self.factory.jobGet(self.bid().bid().ticket())
        else:
            #return self.__job
            return None
        
    def getJobByTicket(self, ticket):
        log.debug("Getjob: '%s'" % (ticket))
        job = self.factory.jobGet(ticket)
        if job is None:
            job = self.__jobList.get(ticket)

        if job is not None:
            log.debug("Got: '%s'" % job.ticket())
        return job

    def allJobNextEvent(self):
        for xbed, job in self.__jobList.iteritems():
            job.nextEvent(self)
        pass
    
    def allJobTerminate(self):
        for xbed, job in self.__jobList.iteritems():
            job.terminate(self)
        pass

    def connectionMade(self):
        log.debug("=====+++ client %s has connected" % (self.client))
        #layer = self.getsecurityLayer()
        cl = self.factory.getClient(self.client)
        if hasattr(cl, "cert"):
            self.__subject = cl.cert().subject()
            log.debug("Have CERT '%s'" % self.__subject)
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
        log.debug("===***=== do_recvPong -> pong is new, save it")
        self.__hasPongs  = True
        pongCtxt = BidContext(pong, xbed)
        self.__xbedid    = xbed.xbedaemon
        self.__auctionBids[self.__xbedid] = pongCtxt
        
    def do_recvBid(self, xbed, bid):
        log.debug("===***=== do_recvBid")
        log.debug("===Price %3.2f Ticket='%s'" % (bid.price(), bid.ticket()))
        log.debug("===***=== do_recvBid -> bid is new, save it")
        self.__hasBids  = True
        bidCtxt = BidContext(bid, xbed)
        xbedid    = xbed.xbedaemon
        self.__auctionBids[xbedid] = bidCtxt
        self.__jobList[xbedid].setBid(bidCtxt)
        self.factory.jobAdd(bid.ticket(), self.__jobList[xbedid])
        log.debug("===***=== do_recvBid -> bid is new, save it done")
         
    def do_recvBrokerError(self, xbed, response):
        log.debug("===***=== do_recvBrokerError '%d'" % response.code())
        self.__hasProviderError    = True
        self.__statusProvider      = response


    #
    def sendReply(self, msg):
        log.debug("sendReply(%s)" % msg.as_xml())
        self.__reply.hasMsg = False #True
        self.__reply.msg = msg
        self.transport.write(msg.as_xml())
        
    def compareBids(self, bid_ctxt_A, bid_ctxt_B):
        if bid_ctxt_A.bid().price() < bid_ctxt_B.bid().price():
          return -1
        if bid_ctxt_A.bid().price() == bid_ctxt_B.bid().price():
          return 0
        return 1

    #
    def getBestBid(self):
        log.debug("getBestBid")
        bestbids = [] # holds a tuple of (bidctxt, xbed)
        log.debug("collecting best bids")
        for xbed, bidCtxt in self.__auctionBids.iteritems():
            if len(bestbids):
              current_best, _ = bestbids[0]
              compare_val = self.compareBids(bidCtxt, current_best)
              if compare_val == 0:
                # remember an equally good bid
                log.debug("found equally good bid=%s" % str(bidCtxt))
                bestbids.append( (bidCtxt, xbed) )
              if compare_val == -1:
                # replace all bids with the new best
                log.debug("replacing current best with new bid=%s" % str(bidCtxt))
                bestbids = [(bidCtxt, xbed)]
            else:
              bestbids = [(bidCtxt, xbed)]
        log.debug("bestbids=%s" % str(bestbids))
        assert len(bestbids), "Could not find best bid, array was empty!"
        bestbid, bestxbed = random.choice(bestbids)

        # update job data
        self.__bestbid_ticket = bestbid.bid().ticket()
        self.__job        = None
        self.__hasBestBid = True
        self.__xbedid    = bestxbed

        # send deny to other xbedaemons
        for xbed, bidCtxt in self.__auctionBids.iteritems():
            if bestxbed != xbed:
                self.sendAuctionDeny(bidCtxt)
        return bestbid

    #
    def messageBooked(self):
        bidCtxt = self.__auctionBids[self.__xbedid]
        bid = bidCtxt.bid()
        return message.BookedResponse(bid.uuid(), self.__xbedid, bid.xbedurl(),
               bid.ticket(), bid.task_id(), bid.price())

    #
    def sendAuctionAccept(self, bidCtxt):
        log.debug("--sendAuctionAccept")
        bid = bidCtxt.bid()
        self.factory.sendAuctionAccept(bidCtxt.xbedproto(), bid.uuid(), bid.ticket(), bid.task_id())

    def sendAuctionDeny(self, bidCtxt):
        log.debug("--sendAuctionDeny")
        bid = bidCtxt.bid()
        self.factory.sendAuctionDeny(bidCtxt.xbedproto(), bid.uuid(), bid.ticket(), bid.task_id())

    def sendConfirmReservation(self, job, msg):
        bidCtxt = job.bidContext()
        self.factory.sendConfirmReservation(bidCtxt.xbedproto(), msg)

    #
    def do_PollRequest(self, elem, *args, **kw):
        log.debug("XenBEEClient2BrokerProtocol::do_PollRequest()")
        log.debug("Current: '%s'" % self.__fsm.getState().getName())
        request = message.MessageBuilder.from_xml(elem.getroottree())
        log.debug("XenBEEClient2BrokerProtocol::do_PollRequest() %s",
                  request.cmd_name())

        reply = self.__reply
        if reply.hasMsg:
            log.debug("do_PollRequest: '%s'" % reply.msg)
            self.__reply.hasMsg = False
            return reply.msg

        log.debug("do_PollRequest: DEFAULT '%s'" % request.cmd_name())
        #return  message.PollResponse(self.client, request.cmd_name())
    
    def do_PingRequest(self, elem, *args, **kw):
        log.debug("XenBEEClient2BrokerProtocol::do_PingRequest()")
        log.debug("Current: '%s'" % self.__fsm.getState().getName())
        request = message.MessageBuilder.from_xml(elem.getroottree())
        self.pushEvent("PingReq")
        msg = message.PollResponse(self.client, "PongResponse")
        log.debug("do_PingRequest: '%s'" % msg)
        return msg

    def do_BookingRequest(self, elem, *args, **kw):
        msg = message.MessageBuilder.from_xml(elem.getroottree())
        log.debug("bookingRequest: ")
        self.pushEvent("BookingReq")
        msg = message.PollResponse(self.client, "BookedResponse")
        log.debug("response (%s)" % msg)
            
    def do_ConfirmReservation(self, elem, *args, **kw):
        log.debug("=============== XenBEEClient2BrokerProtocol::do_ConfirmReservation")
        msgin = message.MessageBuilder.from_xml(elem.getroottree())
        msg =  message.ConfirmReservation(msgin.ticket(), msgin.jsdl(), False)
        job = self.getJobByTicket(msgin.ticket())
        if job is None:
            self.sendReply(message.Error(errcode.TICKET_INVALID, msgin.ticket()))
        else:
            self.sendConfirmReservation(job, msg)

    def do_JobStatusRequest(self, elem, *args, **kw):
        log.debug("=============== XenBEEClient2BrokerProtocol::do_JobStatusRequest")
        msgin = message.MessageBuilder.from_xml(elem.getroottree())
        job = self.getJobByTicket(msgin.ticket())
        if job is None:
            msg = message.Error(errcode.TICKET_INVALID, msgin.ticket())
        else:
            msg = message.JobStatusResponse(msgin.ticket(), job.task(), job.getTime(),
                                            job.getCost(), job.getStart(), job.getEnd(),
                                            job.getState())
            if (job.getState()=='JobFSM.StFinishedClosing'):
                job.do_Event("closeJob_Closed", self)
        #return msg
        self.sendReply(msg)

    def success(self):
        self.sendReply(self._success("Ok"))

    def failure(self, reason):
        self.sendReply(self._failure(reason))

    def _success(self, uid):
        return message.Error(errcode.OK, uid)
    def _failure(self, reason):
        return message.Error(errcode.INTERNAL_SERVER_ERROR, reason)

    #
    #
    def pushEvent(self, event):
        log.debug("=========PUSH(%s)" % event)
        self.__nextTransition.append(event)
        
    def popEvent(self):
        if len(self.__nextTransition) == 0:
            return None #event = "PollReq"
        else:
            event = self.__nextTransition.pop()
        return event

    def setTimeout(self):
        broker = CalanaBrokerDaemon.getInstance()
        self.__requestend = int(broker.opts.bid_timeout) + time.time()

    def checkForEnd(self):
        log.debug("checkForEnd: %d < %d" % (self.__requestend , time.time()))
        if ( self.__requestend < time.time()):
            return True
        if ( self.ReqLen() < self.RespLen()):
            return False
        else:
            return True

    def clearXBEDaemon(self):
        for id, p in self.__xbedaemonTimer.iteritems():
            p = 0

    def addXBEDaemon(self, id):
        #self.__jobList[id] = job.Job(self.factory)
        self.__jobList[id] = job.Job(self)
        self.__jobList[id].setUser(self.__subject)
        self.__xbedaemonTimer[id] = time.time()

    #
    def bid(self):
        return self.__auctionBids[self.__xbedid]

    def hasBestBid(self):
        return self.__hasBestBid

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
    def waitForResponse(self, job, reqCtxt):
        # e.g. can handle timer
        reqCtxt.sendReply(message.PollResponse(self.client, request.cmd_name()))
        log.debug("=== *** XenBEEBrokerProtocolFactory::waitForResponse '%s' " % request.cmd_name())
        
        if (self.__requestend < time.time()):
            reqCtxt.pushEvent("EndReq")
        else:
            reqCtxt.pushEvent("PollReq")

    def waitForAck(self, job, reqCtxt):
        log.debug("XenBEEBrokerProtocolFactory::waitForAck: %d < %d"
                  % (self.__requestend , time.time()))
        
        if (self.__requestend < time.time()):
            reqCtxt.pushEvent("ProviderRejected")
        else:
            if reqCtxt.hasProviderError():
                # evaluate result
                log.debug("WAIT: %d %d" % ( reqCtxt.getProviderErrorCode() , errcode.OK))
                if ( reqCtxt.getProviderErrorCode() == errcode.OK):
                    reqCtxt.pushEvent("ProviderBooked")
                else:
                    reqCtxt.pushEvent("ProviderRejected")
                reqCtxt.clearProviderError()
            else:
                reqCtxt.pushEvent("PollReq")
        
    def waitForConfirm(self, job, reqCtxt):
        log.debug("XenBEEBrokerProtocolFactory::waitForConfirm")
        reqCtxt.sendReply(message.PollResponse(self.client, request.cmd_name()))
        log.debug("=== *** XenBEEBrokerProtocolFactory::waitForResponse '%s' " % request.cmd_name())
        
        log.debug("waitForConfirm: %d < %d" % (self.__requestend , time.time()))
        if (self.__requestend > time.time()):
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
    def inBookingReq(self, job, reqCtxt):
        log.debug("XenBEEBrokerProtocolFactory::inBookingReq")
        self.clearXBEDaemon()
        self.__hasBids    = False

        reqCtxt.setTimeout()

        try:
            self.factory.sendBookingRequest(reqCtxt)
            reqCtxt.allJobNextEvent()
            msg = message.PollResponse(self.client, "BookedResponse")
            reqCtxt.pushEvent("AddBid")
            log.debug("========== Sendet %d bookingRequest" % reqCtxt.ReqLen())
        except Exception, e:
            reqCtxt.pushEvent("EndReq")
            #reqCtxt.allJobTerminate()
            log.debug("inBookingReq Failed: '%s'" % e )
            msg = message.Error(errcode.ILLEGAL_REQUEST, "No XbeDaemons connected. '%s'" % e)

        reqCtxt.sendReply(msg)

    def inAuctionBid(self, job, reqCtxt): #, bid):
        log.debug("inAuctionBid: %d < %d" % (self.__requestend , time.time()))
        if ( reqCtxt.checkForEnd() ):
            # Booking end
            self.pushEvent("EndReq")
        else:
            self.pushEvent("AddBid")
        pass

    def endSuccessfulAuction(self, job, reqCtxt): ##job, brokerCtxt):
        # send do_Cancel to most of xbedaemons
        # do_ConfirmReservation
        log.debug("XenBEEBrokerProtocolFactory::endSuccessfulAuction")
        bidCtxt = reqCtxt.getBestBid()
        reqCtxt.sendAuctionAccept(bidCtxt)
        reqCtxt.setTimeout()
        reqCtxt.pushEvent("PollReq")
        reqCtxt.clearProviderError()
 
    def endFailureAuction(self, job, reqCtxt): ##job, brokerCtxt):
    #def endFailureAuction(self, job, brokerCtxt):
        log.debug("XenBEEBrokerProtocolFactory::endFailureAuction")
        reqCtxt.pushEvent("BookingRejectedAck")
        if job is None:
            reqCtxt.allJobTerminate()
        else:
            job.terminate(reqCtxt)
        log.debug("XenBEEBrokerProtocolFactory::endFailureAuction - done")

    def inProviderBooked(self, job, reqCtxt):
        #def inProviderBooked(self, job, brokerCtxt):
        # send AuctionAccept to the first one,
        # send AuctionDeny to all others
        log.debug("XenBEEBrokerProtocolFactory::inProviderBooked")

        self.sendReply(reqCtxt.messageBooked())
        job.do_Event("endNegotiation", reqCtxt)

    def inProviderBookingRejected(self, job, reqCtxt):
        log.debug("XenBEEBrokerProtocolFactory::inProviderBookingRejected")

        reqCtxt.sendReply(message.Error(errcode.SERVER_BUSY))
        job.do_Event("terminate", reqCtxt)
        reqCtxt.stopFSM()
        #reqCtxt.pushEvent("BookingRejectAck")
        #reply.msg = message.Error(errcode.ILLEGAL_REQUEST, "Ping failed")
        #reply.msg = message.Error(errcode.SERVER_BUSY)

    # do the same for ping
    # send ping to all xenbeeDaemons
    def inPingReq(self, job, reqCtxt):
        log.debug("XenBEEBrokerProtocolFactory::inPingReq for %s" % reqCtxt.client)
        self.clearXBEDaemon()
        self._hasPongs = False

        reqCtxt.setTimeout()
        try:
            self.factory.sendPingRequest(reqCtxt)
            reqCtxt.pushEvent("AddPing")
            msg = message.PollResponse(self.client, "PongResponse")
            log.debug("========== Sendet %d pingRequest" % reqCtxt.ReqLen())
        except Exception, e:
            reqCtxt.pushEvent("EndReq")
            log.debug("inPingReq Failed: '%s'" % e )
            msg = message.Error(errcode.ILLEGAL_REQUEST, "No XbeDaemons connected. '%s'" % e)

        reqCtxt.sendReply(msg)

    def inCollectingPing(self, job, reqCtxt): #, bid):
        log.debug("inCollectingPing: %d < %d" % (self.__requestend , time.time()))
        if ( reqCtxt.checkForEnd() ):
            # Booking end
            self.pushEvent("EndReq")
        else:
            self.pushEvent("AddPing")

        pass
    
    # Have Pong, send pong to xbe Client
    def endFailurePing(self, job, reqCtxt):
        log.debug("=== *** XenBEEBrokerProtocolFactory::endFailurePing")
        reqCtxt.pushEvent("BookingRejectedAck")

    # Have Pong, send pong to xbe Client
    def endSuccessfulPing(self, job, reqCtxt):
        log.debug("=== *** XenBEEBrokerProtocolFactory::endSuccessfulPing")
        if hasattr(message, request.cmd_name()):
            msg = getattr(message, request.cmd_name())("None", 1)
        else:
            msg = message.Error(errcode.ILLEGAL_REQUEST, "No such command")
        reqCtxt.sendReply(msg)
        
    def inConfirm(self, job, reqCtxt):
        log.debug("XenBEEBrokerProtocolFactory::inConfirm")
        msg = self._success("xx")
        reqCtxt.sendReply(msg)

    def inProviderClose(self, job, brokerCtxt):
        log.debug("XenBEEBrokerProtocolFactory::")
        job = brokerCtxt.getJob()
        log.debug("Time for Job: %f", job.getTime())

    def outClose(self, job, brokerCtxt):
        log.debug("XenBEEBrokerProtocolFactory::")
        # send response to client
        
    def inCloseAck(self, job, brokerCtxt):
        log.debug("XenBEEBrokerProtocolFactory::inCloseAck")
        brokerCtxt.stopFSM()

    def inBookingRejectedAck(self, job, reqCtxt):
        log.debug("XenBEEBrokerProtocolFactory::inBookingRejectedAck")
        reqCtxt.stopFSM()
        reqCtxt.sendReply(message.Error(errcode.ILLEGAL_REQUEST, "Request failed"))

    # do the same for ping
    # send ping to all xenbeeDaemons
    def inPingReq(self, job, reqCtxt):
        log.debug("XenBEEBrokerProtocolFactory::inPingReq for %s" % reqCtxt.client)
        self.clearXBEDaemon()
        self._hasPongs = False

        broker = CalanaBrokerDaemon.getInstance()
        self.__requestend = int(broker.opts.bid_timeout) + time.time()
        try:
            self.factory.sendPingRequest(reqCtxt)
            reqCtxt.pushEvent("AddPing")
            msg = message.PollResponse(self.client, "PongResponse")
            log.debug("========== Sendet %d pingRequest" % reqCtxt.ReqLen())
        except Exception, e:
            reqCtxt.pushEvent("EndReq")
            log.debug("inPingReq Failed: '%s'" % e )
            msg = message.Error(errcode.ILLEGAL_REQUEST, "No XbeDaemons connected. '%s'" % e)

        reqCtxt.sendReply(msg)

    def inCollectingPing(self, job, reqCtxt): #, bid):
        log.debug("inCollectingPing: c=%d, t:%d < %d" %
                  (reqCtxt.RespLen(), self.__requestend , time.time()))
        if ( self.__requestend < time.time()):
            # Booking end
            self.pushEvent("EndReq")
        else:
            self.pushEvent("AddPing")

        pass
    
    # Have Pong, send pong to xbe Client
    def endFailurePing(self, job, reqCtxt):
        log.debug("=== *** XenBEEBrokerProtocolFactory::endFailurePing")
        reqCtxt.pushEvent("BookingRejectedAck")

    # Have Pong, send pong to xbe Client
    def endSuccessfulPing(self, job, reqCtxt):
        log.debug("=== *** XenBEEBrokerProtocolFactory::endSuccessfulPing")
        
        #if hasattr(message, request.cmd_name()):
        #    reply.msg = getattr(message, request.cmd_name())("None", 1)
        #else:
        #    reply.msg = message.Error(errcode.ILLEGAL_REQUEST, "No such command")
        reqCtxt.sendReply(message.PongResponse("None", reqCtxt.RespLen()))
        reqCtxt.stopFSM()

    
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
        log.info("send a ping request to xbed '%s' with id '%s'" % (self.xbedaemon , clientProto.client))
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

    #def do_ReservationConfirm(self, err, *args, **kw):
    #    log.debug("======================= do_ReservationConfirm: ")
    #    msg = message.MessageBuilder.from_xml(err.getroottree()) 
    #    self.factory.propagateResponseToJob(msg.ticket, "confirm", self, msg)
    #    self.factory.propagateResponseToClient(msg.uuid(), "Confirm", self, msg)

    #def do_ConfirmAck(self, err, *args, **kw):
    #    log.debug("======================= do_ConfirmAck: ")
    #    msg = message.MessageBuilder.from_xml(err.getroottree()) 
    #    self.factory.propagateResponseToJob(msg.ticket(), "confirm", self, msg)
    #    #self.factory.propagateResponseToClient(msg.uuid(), "Confirm", self, msg)

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
        log.debug("=====> XenBEEBrokerProtocolFactory: Add Job....'%s'" % ticket)
        self.__jobList[ticket] = job
        pass

    def jobGet(self, ticket):
        p = self.__jobList.get(ticket)
        if p is None:
            log.debug("XenBEEBrokerProtocolFactory: no job found '%s' " % ticket)
            return None
        else:
            return p

    def jobEvent(self, ticket, event, reqCtxt):
        log.debug("XenBEEBrokerProtocolFactory jobEvent from '%s' to %s" % (event, ticket))

        p = self.__jobList.get(ticket)
        if p is None:
            log.debug("no job found for '%s'" % ticket)
        else:
            log.debug("propagate event to job. " )
            try:
                clientCtxt = self.getClient(p.uuid())
                p.do_EventByMap(event, clientCtxt)
            except Exception, e:
                pass
            #self.jobEvent(ticket, event, client.protocol)

    def propagateResponseToJob(self, ticket, event, reqCtxt, msg):
        log.debug("Broker:propagate to job '%s' msg '%s'" % (ticket, msg))
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
            log.debug("Client(%s) found at '%s'" % (client, p.protocol))
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
                    p.stopFSM()
                    log.debug("================REMOVE '%s'" % id)
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

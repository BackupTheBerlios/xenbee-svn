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

__version__ = "$Rev: 203 $"
__author__ = "$Author: petry $"

import logging, random, os, time
log = logging.getLogger(__name__)

from textwrap import dedent

from xbe.broker import JobStateMachine_sm

##################################################
##
##################################################
class Job:
    """The job definition

    """
    
    def __init__(self, xbeclient):
        log.debug("Job constructor:")
        self.__fsm = JobStateMachine_sm.JobStateMachine_sm(self)
        self.__fsm.setDebugFlag(2)

        self.__user      = None
        self.__ticket    = None
        self.__task_id   = None

        self.__jobStart  = 0
        self.__jobEnd    = 0
        self.__jobPrice  = 0
        self.__xbeclient = xbeclient

        self.__nextTransition = ["startNegotiation"]

    def bidContext(self):
        return self.__bidCtxt

    def ticket(self):
        return self.__ticket

    def task(self):
        return self.__task_id

    def uuid(self):
        return self.__client_uuid

    def setUser(self, user):
        self.__user = user
        
    def setBid(self, bidCtxt):
        self.__bidCtxt     = bidCtxt
        self.__ticket      = bidCtxt.bid().ticket()
        self.__task_id     = bidCtxt.bid().task_id()
        self.__client_uuid = bidCtxt.bid().uuid()
        self.__jobPrice    = bidCtxt.bid().price()

    def getClientUUID(self):
        return self.__client_uuid
    def getUser(self):
        return self.__user
    def getTime(self):
        if self.getEnd()>0:
            return self.__jobEnd - self.__jobStart
        else:
            return 0
    def getCost(self):
        return self.__jobPrice * (self.getTime())/60
    def getStart(self):
        return self.__jobStart
    def getEnd(self):
        return self.__jobEnd
    def getState(self):
        return self.__fsm.getState().getName()

    # handle next event
    def do_Event(self, event, reqCtxt):
        
        log.debug("JOB '%s' run in state '%s' event '%s'" %
                  (self.ticket(), self.__fsm.getState().getName(), event))
        if hasattr(self.__fsm, event):
            log.debug("Run event '%s'" % event)
            getattr(self.__fsm, event)(self, reqCtxt)
        else:
            log.debug("Event '%s' not found." % event)
            raise CommandFailed("jobFSM: No such Transition '%s'." % event)

    def do_EventByMap(self, eventkey, reqCtxt):
        eventMap = {
            "Pending:Reserved" : 1,
            "Pending:Confirmed" : "confirm",
            "Running:Stage-In"  : "runJob_StageIn",
            "Running:Instance-Starting" : "",
            "Running:Executing"         : "runJob_Execute",
            "Running:Stage-Out"         : "runJob_StageOut",
            "Running:Instance-Stopping" : "",
            "Finished"   : "closeJob_Closing",

            #"Running:Instance-Starting" : "runJob_Execute",
            #"Running:Executing"         : "runJob_StageOut",
            #"Running:Stage-Out"         : "closeJob_Executed",
            #"Running:Instance-Stopping" : "closeJob_Closing",
            #"Finished"   : "closeJob_Closed",
            "Failed"     : "fail",
            "Terminated" : "terminate"
        }
        event = eventMap[eventkey]
        log.debug("=========>do_Event '%s' run in state '%s' even [%s]" % 
                  (self.ticket(), self.__fsm.getState().getName(), event))
        if hasattr(self.__fsm, event):
            try:
                log.debug("Run event '%s'" % event)
                getattr(self.__fsm, event)(self, reqCtxt)
                if (event == "runJob_StageOut" ):
                    self.__fsm.closeJob_Executed(self, reqCtxt)
            except Exception, e:
                log.debug("FAILED: %s." % e)
        else:
            log.debug("Event '%s' not found." % event)
        
    def terminate(self, reqCtxt):
        log.debug("==job.terminate '%s' run in state '%s' event '%s'" %
                  (self.ticket(), self.__fsm.getState().getName(), "terminate"))
        self.__fsm.terminate(self, reqCtxt)
        
    def nextEvent(self, reqCtxt):
        event = self.popEvent()
        log.debug("==job.nextEvent '%s' run event '%s'" %
                  (self.ticket(), event))
        if event is not None:
            if hasattr(self.__fsm, event):
                getattr(self.__fsm, event)(self, reqCtxt)
            else:
                raise CommandFailed("JobFSM, No such Transition '%s'." % self.__nextTransition)
        else:
            raise CommandFailed("JobFSM, No such Transition '%s'." % self.__nextTransition)
            
    def pushEvent(self, event):
        self.__nextTransition.append(event)
        
    def popEvent(self):
        if len(self.__nextTransition) == 0:
            return None #event = "PollReq"
        else:
            event = self.__nextTransition.pop()
         return event

    # implementation of statemachine actions
    def terminateImpl(self, job, cCtxt):
        log.debug("==job::terminateImpl")
        self.__jobEnd = time.time()
        if self.__jobStart == 0:
            self.__jobStart = self.__jobEnd
        self.log_job_closed()
        pass
    
    def failImpl(self, job, cCtxt):
        log.debug("==job::failImpl")
        self.__jobEnd = time.time()
        if self.__jobStart == 0:
            self.__jobStart = self.__jobEnd
        self.log_job_closed()
        pass

    def startNegotiationImpl(self, job, cCtxt):
        log.debug("==job::startNegotiationImpl")
        self.pushEvent("endNegotiation")
        pass

    def endNegotiationImpl(self, job, cCtxt):
        log.debug("==job::endNegotiationImpl")
        bid = cCtxt.bid()
        job.setBid(bid)
        self.print_info()

    def confirmImpl(self, job, cCtxt):
        log.debug("==job::confirmImpl and push event")
        self.__xbeclient.pushEvent("Confirm")

    def	runJob_StageInImpl(self, job, cCtxt):
        log.debug("==job::runJob_StageInImpl")
        self.pushEvent("runJob_Execute")
        self.__jobStart = time.time()
        pass

    def	runJob_ExecuteImpl(self, job, cCtxt):
        log.debug("==job::runJob_ExecuteImpl")
        self.pushEvent("runJob_StageOut")
        pass

    def runJob_StageOutImpl(self, job, cCtxt):
        log.debug("==job::closeJob_Executed")
        self.pushEvent("")
        pass

    def	closeJob_ExecutedImpl(self, job, cCtxt):
        log.debug("==job::closeJob_ExecutedImpl")
        self.pushEvent("closeJob_Closing")
        pass

    def	closeJob_ClosingImpl(self, job, cCtxt):
        log.debug("==job::closeJob_ClosingImpl")
        self.__jobEnd = time.time()
        #cCtxt.success()
        self.__xbeclient.pushEvent("ProviderClose")
        pass

    def closeJob_ClosedImpl(self, job, cCtxt):
        log.debug("==job::closeJob_ClosedImpl")
        log.debug("Job finished: Time: %d sec" % self.getTime())
        self.__xbeclient.pushEvent("CloseAck")
        self.log_job_closed()
        pass

    def log_job_closed(self):
        log.info("Job finished: Ticket:%s Task:%s User:%s Start:%f End:%f Time:%f Price:%f State:%s" % (self.ticket(), self.task(), self.getUser(), self.jobStart(), self.jobEnd(), self.getTime(), self.getCost(), self.getState()))

    def print_info(self):
        print dedent("""\
        ticket:%(ticket)s
        task  :%(task)s
        """ % {"ticket": self.ticket(),
               "task": self.task(),
               }
        )

class JobContext():
    """The job context definition

    """
    def __init__(self, factory, xbed):
        self.__xbed = xbed
        self.__job  = Job(factory)
        pass
    

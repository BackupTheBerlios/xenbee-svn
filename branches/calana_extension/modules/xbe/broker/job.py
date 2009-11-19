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

import logging, random, os
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

        self.__xbeclient = xbeclient

        self.__nextTransition = "startNegotiation"

    def ticket(self):
        return self.__ticket

    def task(self):
        return self.__task_id

    def setUser(self, user):
        self.__user = user
        
    def setBid(self, bid):
        self.__ticket      = bid.ticket()
        self.__task_id     = bid.task_id()
        self.__client_uuid = bid.uuid()

    # handle next event
    def do_Event(self, event, reqCtxt):
        if hasattr(self.__fsm, event):
            log.debug("Run event '%s'" % event)
            getattr(self.__fsm, event)(self, reqCtxt)
        else:
            log.debug("Event '%s' not found." % event)

    def do_EventByMap(self, eventkey, reqCtxt):
        eventMap = {
            "Pending:Reserved" : 1,
            "Pending:Confirmed" : "confirm",
            "Running:Stage-In"  : "runJob_StageIn",
            "Running:Instance-Starting" : "",
            "Running:Executing"         : "runJob_Execute",
            "Running:Stage-Out"         : "runJob_StageOut",
            "Running:Instance-Stopping" : "",
            "Finished"   : "closeJob_Closed",

            #"Running:Instance-Starting" : "runJob_Execute",
            #"Running:Executing"         : "runJob_StageOut",
            #"Running:Stage-Out"         : "closeJob_Executed",
            #"Running:Instance-Stopping" : "closeJob_Closing",
            #"Finished"   : "closeJob_Closed",
            "Failed"     : "fail",
            "Terminated" : "terminate"
        }
        event = eventMap[eventkey]
        log.debug("=========>do_Event[%s]" % event)
        if hasattr(self.__fsm, event):
            log.debug("Run event '%s'" % event)
            getattr(self.__fsm, event)(self, reqCtxt)
            if (event == "runJob_StageOut" ):
                self.__fsm.closeJob_Executed(self, reqCtxt)
                self.__fsm.closeJob_Closing(self, reqCtxt)
        else:
            log.debug("Event '%s' not found." % event)
        
    def terminate(self, reqCtxt):
        log.debug("==job.terminate")
        self.__fsm.terminate(self, reqCtxt)
        
    def nextEvent(self, reqCtxt):
        log.debug("==job.nextEvent")
        event = self.popEvent()
        if event is not None:
            if hasattr(self.__fsm, event):
                getattr(self.__fsm, event)(self, reqCtxt)
            else:
                raise CommandFailed("JobFSM, No such Transition '%s'." % self.__nextTransition)
        else:
            raise CommandFailed("JobFSM, No such Transition '%s'." % self.__nextTransition)
            
    def pushEvent(self, event):
        self.__nextTransition = event
        
    def popEvent(self):
        if self.__nextTransition is None:
            return None #event = "PollReq"
        else:
            event = self.__nextTransition
            self.__nextTransition = None
        return event

    # implementation of statemachine actions
    def terminateImpl(self, job, cCtxt):
        log.debug("==job::terminateImpl")
        pass
    
    def failImpl(self, job, cCtxt):
        log.debug("==job::failImpl")
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
        self.pushEvent("confirm")
        pass

    def confirmImpl(self, job, cCtxt):
        log.debug("==job::confirmImpl")
        self.pushEvent("runJob_StageIn")
        pass

    def	runJob_StageInImpl(self, job, cCtxt):
        log.debug("==job::runJob_StageInImpl")
        self.pushEvent("runJob_Execute")
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
        self.pushEvent("closeJob_Closed")
        pass

    def closeJob_ClosedImpl(self, job, cCtxt):
        log.debug("==job::closeJob_ClosedImpl")
        pass

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
    def __init__(self, factory):
        self.__factory = factory
        self.__fsm     = Job()
        pass
    

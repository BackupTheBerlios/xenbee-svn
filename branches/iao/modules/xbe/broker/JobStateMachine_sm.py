# DO NOT EDIT.
# generated by smc (http://smc.sourceforge.net/)
# from file : JobStateMachine.sm

import statemap

import xbe.broker.proto

class JobStateMachineState(statemap.State):

    def Entry(self, fsm):
        pass

    def Exit(self, fsm):
        pass

    def closeJob_Closed(self, fsm, job, cCtxt):
        self.Default(fsm)

    def closeJob_Closing(self, fsm, job, cCtxt):
        self.Default(fsm)

    def closeJob_Executed(self, fsm, job, cCtxt):
        self.Default(fsm)

    def confirm(self, fsm, job, cCtxt):
        self.Default(fsm)

    def endNegotiation(self, fsm, job, cCtxt):
        self.Default(fsm)

    def fail(self, fsm, job, cCtxt):
        self.Default(fsm)

    def runJob_Execute(self, fsm, job, cCtxt):
        self.Default(fsm)

    def runJob_StageIn(self, fsm, job, cCtxt):
        self.Default(fsm)

    def runJob_StageOut(self, fsm, job, cCtxt):
        self.Default(fsm)

    def startNegotiation(self, fsm, job, cCtxt):
        self.Default(fsm)

    def terminate(self, fsm, job, cCtxt):
        self.Default(fsm)

    def Default(self, fsm):
        msg = "\n\tState: %s\n\tTransition: %s" % (
            fsm.getState().getName(), fsm.getTransition())
        raise statemap.TransitionUndefinedException, msg

class JobFSM_Default(JobStateMachineState):
    pass

class JobFSM_StPendingNew(JobFSM_Default):

    def startNegotiation(self, fsm, job, cCtxt):
        ctxt = fsm.getOwner()
        fsm.getState().Exit(fsm)
        fsm.clearState()
        try:
            ctxt.startNegotiationImpl(job, cCtxt)
        finally:
            fsm.setState(JobFSM.StPendingNegotiating)
            fsm.getState().Entry(fsm)

    def terminate(self, fsm, job, cCtxt):
        ctxt = fsm.getOwner()
        fsm.getState().Exit(fsm)
        fsm.clearState()
        try:
            ctxt.terminateImpl(job, cCtxt)
        finally:
            fsm.setState(JobFSM.StTerminated)
            fsm.getState().Entry(fsm)

class JobFSM_StPendingNegotiating(JobFSM_Default):

    def endNegotiation(self, fsm, job, cCtxt):
        ctxt = fsm.getOwner()
        fsm.getState().Exit(fsm)
        fsm.clearState()
        try:
            ctxt.endNegotiationImpl(job, cCtxt)
        finally:
            fsm.setState(JobFSM.StPendingBooked)
            fsm.getState().Entry(fsm)

    def terminate(self, fsm, job, cCtxt):
        ctxt = fsm.getOwner()
        fsm.getState().Exit(fsm)
        fsm.clearState()
        try:
            ctxt.terminateImpl(job, cCtxt)
        finally:
            fsm.setState(JobFSM.StTerminated)
            fsm.getState().Entry(fsm)

class JobFSM_StPendingBooked(JobFSM_Default):

    def confirm(self, fsm, job, cCtxt):
        ctxt = fsm.getOwner()
        fsm.getState().Exit(fsm)
        fsm.clearState()
        try:
            ctxt.confirmImpl(job, cCtxt)
        finally:
            fsm.setState(JobFSM.StPendingConfirmed)
            fsm.getState().Entry(fsm)

    def terminate(self, fsm, job, cCtxt):
        ctxt = fsm.getOwner()
        fsm.getState().Exit(fsm)
        fsm.clearState()
        try:
            ctxt.terminateImpl(job, cCtxt)
        finally:
            fsm.setState(JobFSM.StTerminated)
            fsm.getState().Entry(fsm)

class JobFSM_StPendingConfirmed(JobFSM_Default):

    def runJob_StageIn(self, fsm, job, cCtxt):
        ctxt = fsm.getOwner()
        fsm.getState().Exit(fsm)
        fsm.clearState()
        try:
            ctxt.runJob_StageInImpl(job, cCtxt)
        finally:
            fsm.setState(JobFSM.StRunning_StageIn)
            fsm.getState().Entry(fsm)

    def terminate(self, fsm, job, cCtxt):
        ctxt = fsm.getOwner()
        fsm.getState().Exit(fsm)
        fsm.clearState()
        try:
            ctxt.terminateImpl(job, cCtxt)
        finally:
            fsm.setState(JobFSM.StTerminated)
            fsm.getState().Entry(fsm)

class JobFSM_StRunning_StageIn(JobFSM_Default):

    def fail(self, fsm, job, cCtxt):
        ctxt = fsm.getOwner()
        fsm.getState().Exit(fsm)
        fsm.clearState()
        try:
            ctxt.failImpl(job, cCtxt)
        finally:
            fsm.setState(JobFSM.StFailed)
            fsm.getState().Entry(fsm)

    def runJob_Execute(self, fsm, job, cCtxt):
        ctxt = fsm.getOwner()
        fsm.getState().Exit(fsm)
        fsm.clearState()
        try:
            ctxt.runJob_ExecuteImpl(job, cCtxt)
        finally:
            fsm.setState(JobFSM.StRunning_Executing)
            fsm.getState().Entry(fsm)

    def terminate(self, fsm, job, cCtxt):
        ctxt = fsm.getOwner()
        fsm.getState().Exit(fsm)
        fsm.clearState()
        try:
            ctxt.terminateImpl(job, cCtxt)
        finally:
            fsm.setState(JobFSM.StTerminated)
            fsm.getState().Entry(fsm)

class JobFSM_StRunning_Executing(JobFSM_Default):

    def fail(self, fsm, job, cCtxt):
        ctxt = fsm.getOwner()
        fsm.getState().Exit(fsm)
        fsm.clearState()
        try:
            ctxt.failImpl(job, cCtxt)
        finally:
            fsm.setState(JobFSM.StFailed)
            fsm.getState().Entry(fsm)

    def runJob_StageOut(self, fsm, job, cCtxt):
        ctxt = fsm.getOwner()
        fsm.getState().Exit(fsm)
        fsm.clearState()
        try:
            ctxt.runJob_StageOutImpl(job, cCtxt)
        finally:
            fsm.setState(JobFSM.StRunning_StageOut)
            fsm.getState().Entry(fsm)

    def terminate(self, fsm, job, cCtxt):
        ctxt = fsm.getOwner()
        fsm.getState().Exit(fsm)
        fsm.clearState()
        try:
            ctxt.terminateImpl(job, cCtxt)
        finally:
            fsm.setState(JobFSM.StTerminated)
            fsm.getState().Entry(fsm)

class JobFSM_StRunning_StageOut(JobFSM_Default):

    def closeJob_Executed(self, fsm, job, cCtxt):
        ctxt = fsm.getOwner()
        fsm.getState().Exit(fsm)
        fsm.clearState()
        try:
            ctxt.closeJob_ExecutedImpl(job, cCtxt)
        finally:
            fsm.setState(JobFSM.StFinishedExecuted)
            fsm.getState().Entry(fsm)

    def terminate(self, fsm, job, cCtxt):
        ctxt = fsm.getOwner()
        fsm.getState().Exit(fsm)
        fsm.clearState()
        try:
            ctxt.terminateImpl(job, cCtxt)
        finally:
            fsm.setState(JobFSM.StTerminated)
            fsm.getState().Entry(fsm)

class JobFSM_StFinishedExecuted(JobFSM_Default):

    def closeJob_Closing(self, fsm, job, cCtxt):
        ctxt = fsm.getOwner()
        fsm.getState().Exit(fsm)
        fsm.clearState()
        try:
            ctxt.closeJob_ClosingImpl(job, cCtxt)
        finally:
            fsm.setState(JobFSM.StFinishedClosing)
            fsm.getState().Entry(fsm)

class JobFSM_StFinishedClosing(JobFSM_Default):

    def closeJob_Closed(self, fsm, job, cCtxt):
        ctxt = fsm.getOwner()
        fsm.getState().Exit(fsm)
        fsm.clearState()
        try:
            ctxt.closeJob_ClosedImpl(job, cCtxt)
        finally:
            fsm.setState(JobFSM.StFinishedClosed)
            fsm.getState().Entry(fsm)

class JobFSM_StFinishedClosed(JobFSM_Default):
    pass

class JobFSM_StTerminated(JobFSM_Default):
    pass

class JobFSM_StFailed(JobFSM_Default):
    pass

class JobFSM:

    StPendingNew = JobFSM_StPendingNew('JobFSM.StPendingNew', 0)
    StPendingNegotiating = JobFSM_StPendingNegotiating('JobFSM.StPendingNegotiating', 1)
    StPendingBooked = JobFSM_StPendingBooked('JobFSM.StPendingBooked', 2)
    StPendingConfirmed = JobFSM_StPendingConfirmed('JobFSM.StPendingConfirmed', 3)
    StRunning_StageIn = JobFSM_StRunning_StageIn('JobFSM.StRunning_StageIn', 4)
    StRunning_Executing = JobFSM_StRunning_Executing('JobFSM.StRunning_Executing', 5)
    StRunning_StageOut = JobFSM_StRunning_StageOut('JobFSM.StRunning_StageOut', 6)
    StFinishedExecuted = JobFSM_StFinishedExecuted('JobFSM.StFinishedExecuted', 7)
    StFinishedClosing = JobFSM_StFinishedClosing('JobFSM.StFinishedClosing', 8)
    StFinishedClosed = JobFSM_StFinishedClosed('JobFSM.StFinishedClosed', 9)
    StTerminated = JobFSM_StTerminated('JobFSM.StTerminated', 10)
    StFailed = JobFSM_StFailed('JobFSM.StFailed', 11)
    Default = JobFSM_Default('JobFSM.Default', -1)

class JobStateMachine_sm(statemap.FSMContext):

    def __init__(self, owner):
        statemap.FSMContext.__init__(self, JobFSM.StPendingNew)
        self._owner = owner
        self.setState(JobFSM.StPendingNew)
        JobFSM.StPendingNew.Entry(self)

    def closeJob_Closed(self, *arglist):
        self._transition = 'closeJob_Closed'
        self.getState().closeJob_Closed(self, *arglist)
        self._transition = None

    def closeJob_Closing(self, *arglist):
        self._transition = 'closeJob_Closing'
        self.getState().closeJob_Closing(self, *arglist)
        self._transition = None

    def closeJob_Executed(self, *arglist):
        self._transition = 'closeJob_Executed'
        self.getState().closeJob_Executed(self, *arglist)
        self._transition = None

    def confirm(self, *arglist):
        self._transition = 'confirm'
        self.getState().confirm(self, *arglist)
        self._transition = None

    def endNegotiation(self, *arglist):
        self._transition = 'endNegotiation'
        self.getState().endNegotiation(self, *arglist)
        self._transition = None

    def fail(self, *arglist):
        self._transition = 'fail'
        self.getState().fail(self, *arglist)
        self._transition = None

    def runJob_Execute(self, *arglist):
        self._transition = 'runJob_Execute'
        self.getState().runJob_Execute(self, *arglist)
        self._transition = None

    def runJob_StageIn(self, *arglist):
        self._transition = 'runJob_StageIn'
        self.getState().runJob_StageIn(self, *arglist)
        self._transition = None

    def runJob_StageOut(self, *arglist):
        self._transition = 'runJob_StageOut'
        self.getState().runJob_StageOut(self, *arglist)
        self._transition = None

    def startNegotiation(self, *arglist):
        self._transition = 'startNegotiation'
        self.getState().startNegotiation(self, *arglist)
        self._transition = None

    def terminate(self, *arglist):
        self._transition = 'terminate'
        self.getState().terminate(self, *arglist)
        self._transition = None

    def getState(self):
        if self._state == None:
            raise statemap.StateUndefinedException
        return self._state

    def getOwner(self):
        return self._owner


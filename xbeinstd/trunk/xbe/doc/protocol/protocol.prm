mtype = {LifeSign, Execute, ExecuteAck, Terminate, TerminateAck, Finished, FinishedAck, Status, StatusReq, Start, Shutdown};
xenMsgs = {Start, Stopped, Failed}
chan toXbed = [1] of {mtype};
chan toInst = [1] of {mtype};
chan xend = [0] of {mtype};

byte done = 0;

proctype Inst(chan in, out)
{
  if
  :: in ? Start -> goto StDown;
  :: timeout -> goto StFailed;
  fi;

StDown:
  if
  :: true -> out ! LifeSign; goto StIdle;
  :: true -> goto StFailed;
  fi;

StIdle:
  if
  :: in ? Execute -> goto StBusy;
  :: in ? StatusReq -> out ! Status; goto StIdle;
  :: true -> out ! LifeSign; goto StIdle;
  :: true -> goto StFailed;
  fi;

StBusy:
  if
  :: true -> out ! LifeSign; goto StBusy;
  :: in ? StatusReq -> out ! Status; goto StBusy;
  :: true -> out ! Finished; goto StFinished;
  :: true -> goto StFailed;
  fi;

StFailed:  
StFinished:
  atomic { done = done + 1; }
}

proctype Xbed(chan in, out)
{
StPendingReserved:
  if
  /* model user interaction */
  :: true -> goto StPendingConfirmed;
  :: true -> goto StTerminated;
  fi;
StPendingConfirmed:
  if
  :: true -> goto StTerminated;
  :: true -> goto StInstanceStarting;
  fi;
StInstanceStarting:
  out ! Start;
  if
  :: in ? LifeSign -> goto StIdle;
  :: timeout -> goto StFailed;
  fi;
StIdle:
  if
  :: in ? LifeSign -> 
      if
      :: true -> goto StIdle;
      :: true -> out ! StatusReq;
           do
           :: in ? Status -> goto StIdle;
           :: in ? LifeSign -> true;
           od;
      :: true -> out ! Execute; goto StBusy;
      fi;
  :: timeout -> goto StFailed;
  fi;
StBusy:
  if
  :: in ? LifeSign -> goto StBusy;
  :: in ? Finished -> goto StFinished;
  :: timeout -> 
      if
      :: true -> goto StFailed;
      :: true -> out ! StatusReq;
         if
         :: in ? Status -> goto StBusy;
         :: timeout -> goto StFailed;
         fi;
      fi;
  fi;
StFinished:
  if
  :: in ? LifeSign -> goto StFinished;
  :: timeout -> goto StTerminated;
  fi;
StFailed:
StTerminated:
StDone:
  atomic { done = done + 1; }
}

init {
  chan c[2] = [1] of {mtype};
  atomic { run Xbed(c[0], c[1]); run Inst(c[1], c[0]) };
  do
  :: (done == 2) -> break;
  od;
}

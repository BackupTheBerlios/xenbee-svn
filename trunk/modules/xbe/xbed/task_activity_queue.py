"""An activity queue, that can be used to store activities for several tasks."""

import sys, os, time, threading, logging
log = logging.getLogger(__name__)

from xbe.util.activity import HOOK_ALL

class ActivityQueue:
    def __init__(self):
        self._cv = threading.Condition()
        self._workerFinished = threading.Condition()
        self._activities = {}
        self._stopped = False
        self._worker = threading.Thread(target=self._activityLoop)
        self._worker.setDaemon(True)
        self._worker.start()
        
    def _notify_me(self, *args, **kw):
        try:
            self._cv.acquire()
            self._cv.notifyAll()
        finally:
            self._cv.release()
        
    def registerActivity(self, task, activity, on_finish, on_fail, on_abort):
        try:
            self._cv.acquire()
            if not self._activities.has_key(task.id()):
                self._activities[task.id()] = []
            self._activities[task.id()].append((activity,
                                                on_finish, on_fail, on_abort))
            activity.addHook(HOOK_ALL, self._notify_me)
            self._cv.notify()
        finally:
            self._cv.release()

    def abortActivities(self, task, wait=True):
        try:
            self._cv.acquire()
            log.debug("aborting activities for task %s" % (str(task.id())))
            acts = self._activities.pop(task.id())
            self._cv.notify()
        finally:
            self._cv.release()

        if not wait:
            return
        
        for act, on_finish, on_fail, on_abort in acts:
            act.abort()
            while not act.done():
                time.sleep(0.5)
            try:
                act.undo()
            except Exception, e:
                log.debug("undo of %s failed" % repr(act))
            if on_abort is not None:
                on_abort(act.getResult())

    def __del__(self):
        try:
            self._cv.acquire()
            self._stopped = True
            self._cv.notify()
        finally:
            self._cv.release()
        try:
            self._workerFinished.acquire()
            self._workerFinished.wait()
        finally:
            self._workerFinished.release()

    def _activityLoop(self):
        cv = self._cv
        try:
            cv.acquire()
            while not self._stopped:
                # wait for activities
                while not len(self._activities):
                    cv.wait()                
                
                for acts in self._activities.values():
                    to_be_removed = []
                    for act in acts:
                        if not act[0].done() and act[0].startable():
                            log.debug("starting %s" % repr(act[0]))
                            act[0].start()
                        elif act[0].finished():
                            to_be_removed.append( (act, act[1]) )
                        elif act[0].failed():
                            to_be_removed.append( (act, act[2]) )
                        elif act[0].aborted():
                            to_be_removed.append( (act, act[3]) )
                            
                    # remove activities
                    if len(to_be_removed):
                        log.debug("removing %d done activities" % len(to_be_removed))
                        map(acts.remove, [tbr[0] for tbr in to_be_removed])

                    # call callbacks
                    try:
                        cv.release()
                        for act, cb in to_be_removed:
                            if cb is not None:
                                try:
                                    cb(act[0].getResult())
                                except Exception, e:
                                    log.debug("activity callback failed:", e)
                    finally:
                        cv.acquire()
                cv.wait(10)
        except Exception, e:
            log.warn("exception in thread loop", e)
        finally:
            try:
                cv.release()
            except:
                pass

        try:
            self._workerFinished.acquire()
            self._workerFinished.notify()
        finally:
            self._workerFinished.release()

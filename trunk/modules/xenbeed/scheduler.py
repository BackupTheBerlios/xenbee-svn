#!/usr/bin/env python
"""
The Xen Based Execution Environment Scheduler
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging, threading, sys
log = logging.getLogger(__name__)

# Twisted imports
from twisted.internet import reactor, task
from twisted.python import failure

class Scheduler:
    """The XenBee scheduler."""

    def __init__(self, taskMgr):
	"""Initialize the scheduler."""
        self.__mtx = threading.RLock()

        self.tMgr = taskMgr
        self.tMgr.addObserver(self.taskWatch)

        self.schedulerLoop = task.LoopingCall(self.cycle)

        self.__maxActiveInstances = 3

        self.__created = []
        self.__preparing = []
        self.__pending = []
        self.__starting = []
        self.__started = []
        self.__finished = []
        self.__failed = []

        self.schedulerLoop.start(.5)

    def logStatistics(self):
        from textwrap import dedent
        log.info(dedent("""
        Scheduling statistics
        =====================

             state    | #tasks
        --------------+---------
        created (new) |   %d
        preparing     |   %d
        pending       |   %d
        starting      |   %d
        started       |   %d
        finished      |   %d
        failed        |   %d
        """ % (len(self.__created),
               len(self.__preparing),
               len(self.__pending),
               len(self.__starting),
               len(self.__started),
               len(self.__finished),
               len(self.__failed))))

    def taskWatch(self, task, event, *args, **kw):
        try:
            self.lock()
            if event == "newTask":
                log.debug("a new task has been created")
                self.__created.append(task)
            elif event == "taskFinished":
                log.debug("task %s finished" % task.ID())
                self.__started.remove(task)
                self.__finished.append(task)
        finally:
            self.unlock()

    def lock(self):
        self.__mtx.acquire()

    def unlock(self):
        self.__mtx.release()

    def cycle(self):
        try:
            self._cycle()
        except:
            log.exception()

    def _cycle(self):
        # prepare newly created tasks (i.e. retrieve neccessary files etc.)
        for task in self.__created:
            try:
                self.lock()

                log.info("preparing task: " + task.ID())
                self.__created.remove(task)
                self.__preparing.append(task)

                def _f(err):
                    self.lock()
                    self.__preparing.remove(task)
                    # XXX: task has failed
                    self.unlock()
                    self.taskFailed(task, err)
                task.prepare().addCallback(self.taskPrepared).addErrback(_f)
            finally:
                self.unlock()

        for task in self.__pending:
            if self.__maxActiveInstances and \
                   len(self.__started) < self.__maxActiveInstances:
                self.lock()
                log.info("starting up instance for task: "+task.ID())

                self.__pending.remove(task)
                self.__starting.append(task)

                def instanceStartupFailed(err, t):
                    log.debug("instance starting failed: %s" % err)
                    self.lock()
                    self.__starting.remove(t)
                    self.unlock()
                    self.taskFailed(t, err)
                    err.clean()
                    return t
                
                d = task.startInstance()
                d.addCallback(self.taskCanBeExecuted)
                d.addErrback(instanceStartupFailed, task)
                self.unlock()

    def taskPrepared(self, task):
        try:
            try:
                self.lock()
                log.info("task %s has been prepared, moving it from preparing to pending" % (task.ID(),))
                self.__preparing.remove(task)
                self.__pending.append(task)
            finally:
                self.unlock()
        except:
            log.exception()
            return failure.Failure()

    def taskCanBeExecuted(self, task):
        try:
            try:
                self.lock()
                log.info("task %s can now be executed" % (task.ID(),))
                self.__starting.remove(task)
                self.__started.append(task)
                log.info("starting task %s" % task.ID())
                task.execute()
            finally:
                self.unlock()
        except Exception, e:
            log.exception(e)
            return failure.Failure()
        return task

    def taskFailed(self, task, err):
        log.info("task %s failed: %s" % (task.ID(),err.getErrorMessage()))
        self.__failed.append(task)

    def __synchronize(self, func, *args, **kw):
        try:
            self.lock()
            rv = func(*args, **kw)
        finally:
            self.unlock()
        return rv

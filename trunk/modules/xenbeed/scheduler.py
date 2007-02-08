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

    def debug(self, event):
        self.logStatistics()
        log.debug("%s: mtx_locked: %s, thread: %s" % (event, self.__mtx._is_owned(), self.__mtx._RLock__owner))

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
        finally:
            self.unlock()

    def lock(self):
        self.debug("LOCKING")
        self.__mtx.acquire()
        self.debug("LOCKED")

    def unlock(self):
        self.debug("UN-LOCKING")
        self.__mtx.release()
        self.debug("UN-LOCKED")

    def cycle(self):
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
                task.prepare().addCallbacks(self.taskPrepared, _f)
            finally:
                self.unlock()

        for task in self.__pending:
            if self.__maxActiveInstances and \
                   len(self.__started) < self.__maxActiveInstances:
                self.lock()
                log.info("starting up instance for task: "+task.ID())

                try:
                    self.__pending.remove(task)
                    self.__starting.append(task)
                except Exception, e:
                    log.exception(e)
                    raise

                def _f(err):
                    self.lock()
                    self.__starting.remove(task)
                    self.unlock()
                    self.taskFailed(task, err)
                task.startInstance().addCallbacks(self.taskCanBeExecuted, _f)
                self.unlock()

    def taskPrepared(self, task):
        try:
            self.lock()
            log.info("task %s has been prepared, moving it from preparing to pending" % (task.ID(),))
            self.__preparing.remove(task)
            self.__pending.append(task)
        finally:
            self.unlock()

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
            raise

    def taskFailed(self, task, err):
        log.info("task %s failed" % (task.ID(),err.getErrorMessage()))
        self.__failed.append(task)

    def __synchronize(self, func, *args, **kw):
        try:
            self.lock()
            rv = func(*args, **kw)
        finally:
            self.unlock()
        return rv

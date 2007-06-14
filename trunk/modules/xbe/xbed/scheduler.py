#!/usr/bin/env python

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

        self.schedulerLoop = task.LoopingCall(self.cycle)

        self.__maxPreparing = 3
        self.__maxActiveInstances = 3
        self.__activeInstances = 0

        self.__created = []
        self.__preparing = []
        self.__pending = []
        self.__starting = []
        self.__started = []
        self.__finished = []
        self.__failed = []

        # scheduler is currently disabled
        #self.tMgr.addObserver(self.taskWatch)
        #self.schedulerLoop.start(0.5)

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
        --------------+---------
        active        |   %d
        """ % (len(self.__created),
               len(self.__preparing),
               len(self.__pending),
               len(self.__starting),
               len(self.__started),
               len(self.__finished),
               len(self.__failed),
               self.__activeInstances)))

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
                self.__activeInstances -= 1
            self.logStatistics()
        finally:
            self.unlock()

    def lock(self):
        self.__mtx.acquire()

    def unlock(self):
        self.__mtx.release()

    def cycle(self):
        try:
            self._cycle()
        except Exception, e:
            log.exception("exception in scheduler loop:")

    def _cycle(self):
        # prepare newly created tasks (i.e. retrieve neccessary files etc.)
        for task in self.__created:
            if self.__maxPreparing and len(self.__preparing) >= self.__maxPreparing:
                break
            try:
                self.lock()

                log.info("preparing task: " + task.ID())
                self.__created.remove(task)
                self.__preparing.append(task)

                self.logStatistics()

                def _f(err):
                    self.lock()
                    self.__preparing.remove(task)
                    # XXX: task has failed
                    self.unlock()
                    task.failed(err)
                task.prepare().addCallback(self.taskPrepared).addErrback(_f)
            finally:
                self.unlock()

        for task in self.__pending:
            if self.__maxActiveInstances and \
                   self.__activeInstances < self.__maxActiveInstances:
                self.lock()
                log.info("starting up instance for task: "+task.ID())

                self.__pending.remove(task)
                self.__starting.append(task)
                self.__activeInstances += 1
                self.logStatistics()

                def instanceStartupFailed(err, t):
                    log.debug("instance starting failed: %s" % err)
                    self.lock()
                    self.__starting.remove(t)
                    self.unlock()
                    def dec_active(arg):
                        self.__activeInstances -= 1
                        return arg
                    
                    t.failed(err).addCallback(dec_active).addCallback(self.taskFailed, err)
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
        log.info("task %s failed:\n%s\n%s" % (task.ID(),err.getErrorMessage(), err.getTraceback()))
        self.__failed.append(task)
        self.logStatistics()

    def __synchronize(self, func, *args, **kw):
        try:
            self.lock()
            rv = func(*args, **kw)
        finally:
            self.unlock()
        return rv

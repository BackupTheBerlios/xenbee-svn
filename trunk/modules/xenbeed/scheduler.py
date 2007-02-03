#!/usr/bin/env python
"""
The Xen Based Execution Environment Scheduler
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging
log = logging.getLogger(__name__)

from xenbeed.instance import InstanceManager

# Twisted imports
from twisted.internet import reactor, task

class Scheduler:
    """The XenBee scheduler."""
    
    def __init__(self, instMgr, taskMgr):
	"""Initialize the scheduler."""
        self.iMgr = instMgr
        self.tMgr = taskMgr
        self.schedulerLoop = task.LoopingCall(self.cycle)
        self.schedulerLoop.start(.5)

        self.__maxActiveInstances = 3

        self.__preparing = []
        self.__pending = []
        self.__started = []
        self.__finished = []

    def cycle(self):
        for task in self.tMgr.tasks.values():
            if task.state() == "created":
                log.info("preparing task: " + task.ID())
                self.__preparing.append(task)
                defer = self.tMgr.prepareTask(task)

                def _s(*args):
                    log.info("moving task from preparing to pending")
                    self.__preparing.remove(task)
                    self.__pending.append(task)
                def _f(err):
                    self.__preparing.remove(task)
                defer.addCallbacks(_s,_f)
            if task.state() == "pending": # and task.startable():
                if self.__maxActiveInstances and len(self.__started) < self.__maxActiveInstances:
                    log.info("starting instance for task: "+task.ID())
                    self.iMgr.lookupByID(task.inst_id).start()
                    task.start()

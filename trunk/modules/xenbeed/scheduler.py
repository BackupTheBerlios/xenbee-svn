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
        self.__im = instMgr
        self.__tm = taskMgr
        self.schedulerLoop = task.LoopingCall(self.cycle)
        self.schedulerLoop.start(.5)

        self.__maxActiveInstances = 3

        self.__preparing = []
        self.__pending = []
        self.__started = []
        self.__finished = []

    def cycle(self):
        for task in self.__tm.tasks.values():
            if task.state() == "created":
                log.info("preparing task: " + task.ID())
                self.__preparing.append(task)
                defer = self.__tm.prepareTask(task)

                def _s(*args):
                    self.__preparing.remove(task)
                    self.__pending.append(task)
                def _f(err):
                    self.__preparing.remove(task)
                defer.addCallbacks(_s,_f)
            if task.state() == "pending":# and task.startable():
                if self.__maxActiveInstances and len(self.__started) < self.__maxActiveInstances:
                    log.info("starting instance for task: "+task.ID())

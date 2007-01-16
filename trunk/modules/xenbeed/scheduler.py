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
    
    def __init__(self, instMgr):
	"""Initialize the scheduler."""
        self.instanceManager = instMgr
        self.task = task.LoopingCall(self.cycle)
        self.task.start(1.0)

    def cycle(self):
        for inst in self.instanceManager:
            if inst.startable():
                log.info("starting instance: "+inst.getName())
                def _s(x):
                    log.info("instance started")
                def _f(f):
                    log.debug("starting failed")
                inst.start().addCallbacks(_s,_f)

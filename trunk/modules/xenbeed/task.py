"""
The XenBEE task module

contains:
    TaskManager:
	used to create new tasks
	manages all currently known tasks
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging, time
log = logging.getLogger(__name__)

try:
    from traceback import format_exc as format_exception
except:
    from traceback import format_exception

from xenbeed.exceptions import *
from xenbeed import util
from xenbeed import fsm

class TaskError(XenBeeException):
    pass

class Task:
    def __init__(self, ID, mgr):
        """Initialize a new task."""
        self._id = ID
        self._tstamp = time.time()
        self.mgr = mgr

        # build FSM
        m = fsm.FSM()
        m.newState("created.pending")
        m.setStartState("created.pending")

        self.fsm = m

    def ID(self):
        """Return the ID for this task."""
        return self._id

class TaskManager:
    """The task-manager.

    Through this class every known task can be controlled:
	- create new tasks

    """
    def __init__(self, base_path="/srv/xen-images/xenbee"):
        """Initialize the TaskManager."""
        self.tasks = {}

    def newTask(self):
        """Returns a new task."""
        from xenbeed.uuid import uuid
        task = Task(uuid(), self)
        self.tasks[task.ID()] = task
        return task

    def removeTask(self, task):
        """Remove the 'task' from the manager."""
        self.tasks.pop(task.ID())
        task.mgr = None

    def lookupByID(self, ID):
        """Return the task for the given ID.

        returns the task object or None

        """
        return self.tasks.get(ID)

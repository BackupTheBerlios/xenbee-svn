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

class TaskError(XenBeeException):
    pass

class Task:
    def __init__(self, ID):
        """Initialize a new task."""
	self._id = ID
	self._tstamp = time.time()
	self.mgr = None

    def ID(self):
        """Return the ID for this task."""
        return self._id

class TaskManager:
    """The task-manager.

    Through this class every known task can be controlled:
	- create a new tasks

    """
    def __init__(self):
        """Initialize the TaskManager."""
        self.tasks = {}

    def newTask(self):
        """Returns a new task."""
        from xenbeed.uuid import uuid
	task = Task(uuid())
        self.tasks[task.ID()] = task
	task.mgr = self
        return task

    def removeTask(self, task):
        """Remove the 'task' from the manager."""
        self.tasks.pop(task.ID())
	task.mgr = None

    def lookupByID(self, ID):
        """Return the task for the given ID.

        returns the task object or None

        """
        return self.tasks.get(ID, None)


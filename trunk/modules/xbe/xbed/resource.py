"""
A module used to gather resources for some task.
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging, time
log = logging.getLogger(__name__)

import threading
from twisted.internet import threads, defer
from twisted.python import failure

class ResourceGatherer(object):
    """I gather several resources for a given task.

    The gathering process can explicitly stopped by the user or due to
    some failure.
    """


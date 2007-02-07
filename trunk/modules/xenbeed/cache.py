"""
The Xen Based Execution Environment - Chache implementation
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging
log = logging.getLogger(__name__)

from xenbeed.uuid import uuid

class Cache(object):
    """A `cache' that stores images and other files (kernel, initrd).

    The cache uses a specific spool directory and a database which
    holds fast lookup information (type of data).

    The stored files are annotated with information provided by the
    user himself, such as the type of the file (image, kernel, initrd,
    etc.) and more specific information like operating system, exact
    version.

    """

    def __init__(self, _dir):
        self.__cacheDir = _dir
        # initDB
        # 
        pass

    def _initDB(self):
        pass

    def cache(self, uri, meta={}):
        pass

"""
The Xen Based Execution Environment - Database connection
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging, os
log = logging.getLogger(__name__)

# use sqlite
from pysqlite2 import dbapi2 as dbapi

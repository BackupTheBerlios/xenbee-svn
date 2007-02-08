"""
The Xen Based Execution Environment - Database connection
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging, os
log = logging.getLogger(__name__)

# use sqlite
try:
    from pysqlite3 import dbapi2 as dbapi
except:    
    from pysqlite2 import dbapi2 as dbapi

"""
	The XenBEE daemon module
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

# start logging

import logging, logging.handlers
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s [%(process)d:%(threadName)s] %(name)s: %(levelname)-8s %(message)s',
                    filename='/tmp/xenbeed.log',
                    filemode='a')
_syslogHdlr = logging.handlers.SysLogHandler()
_syslogHdlr.setLevel(logging.INFO)
_syslogHdlr.setFormatter(logging.Formatter('[%(process)d:%(threadName)s] %(name)-12s: %(levelname)-8s %(message)s'))
logging.getLogger('').addHandler(_syslogHdlr)

logging.info('logging initialized')

def TestSuite():
    import unittest, xenbeed.config, xenbeed.staging
    import xenbeed.test_instance
    import xenbeed.test_util
    import xenbeed.test_disk

    s = []
    s.append(xenbeed.config.TestSuite())
    s.append(xenbeed.staging.TestSuite())
    s.append(xenbeed.test_instance.suite())
    s.append(xenbeed.test_util.suite())
    s.append(xenbeed.test_disk.suite())
    return unittest.TestSuite(s)

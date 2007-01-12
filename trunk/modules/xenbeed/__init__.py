"""
	The XenBEE daemon module
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

# start logging

import logging, logging.handlers, sys

if sys.hexversion >= 0x2040200:
	# treadName available
	thread = ":%(threadName)s"
else:
	thread = ""

_fileHdlr = logging.FileHandler('/tmp/xenbeed.log', 'a')
_fileHdlr.setLevel(logging.DEBUG)
#_fileHdlr.setFormatter(logging.Formatter('%(asctime)s [%(process)d:%(threadName)s] %(name)s: %(levelname)-8s %(message)s'))
_fileHdlr.setFormatter(logging.Formatter('%(asctime)s [%(process)d]' + thread + ' %(name)s:%(lineno)d %(levelname)-8s %(message)s'))
logging.getLogger().addHandler(_fileHdlr)

_syslogHdlr = logging.handlers.SysLogHandler()
_syslogHdlr.setLevel(logging.WARN)
_syslogHdlr.setFormatter(logging.Formatter('[%(process)d]' + thread + ' %(name)-12s: %(levelname)-8s %(message)s'))
logging.getLogger().addHandler(_syslogHdlr)
logging.getLogger().setLevel(logging.DEBUG)

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

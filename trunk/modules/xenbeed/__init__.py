"""
	The XenBEE daemon module
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

# start logging

import logging, logging.handlers, sys

def initLogging(logfile='/tmp/xenbeed.log'):
    if sys.hexversion >= 0x2040200:
	# treadName available
	thread = ":%(threadName)s"
    else:
	thread = ""

    _fileHdlr = logging.FileHandler(logfile, 'a')
    _fileHdlr.setLevel(logging.DEBUG)
    _fileHdlr.setFormatter(logging.Formatter('%(asctime)s [%(process)d]' + thread + ' %(name)s %(levelname)-8s %(message)s'))
    logging.getLogger().addHandler(_fileHdlr)

    _syslogHdlr = logging.handlers.SysLogHandler()
    _syslogHdlr.setLevel(logging.WARN)
    _syslogHdlr.setFormatter(logging.Formatter('[%(process)d]' + thread + ' %(name)-12s: %(levelname)-8s %(message)s'))
    logging.getLogger().addHandler(_syslogHdlr)

    _stderrHdlr = logging.StreamHandler(sys.stderr)
    _stderrHdlr.setLevel(logging.ERROR)
    _stderrHdlr.setFormatter(logging.Formatter('[%(process)d]' + thread + ' %(name)-12s: %(levelname)-8s %(message)s'))
    logging.getLogger().addHandler(_stderrHdlr)

    # activate overall logging of messages with DEBUG-level
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

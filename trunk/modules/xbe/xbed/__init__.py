"""
	The XenBEE daemon module
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

def TestSuite():
    import unittest
    import xbe.xbed.config
    import xbe.xbed.test_instance
    import xbe.util.test_util
    import xbe.util.test_disk
    import xbe.util.staging

    s = []
    s.append(xbe.xbed.config.TestSuite())
    s.append(xbe.util.staging.TestSuite())
    s.append(xbe.xbed.test_instance.suite())
    s.append(xbe.util.test_util.suite())
    s.append(xbe.util.test_disk.suite())
    return unittest.TestSuite(s)

"""
	The XenBEE daemon module
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

def TestSuite():
    import unittest, xenbeed.config, xenbeed.staging
    import xenbeed.test_instance
    import xenbeed.test_util

    s = []
    s.append(xenbeed.config.TestSuite())
    s.append(xenbeed.staging.TestSuite())
    s.append(xenbeed.test_instance.suite())
    s.append(xenbeed.test_util.suite())
    return unittest.TestSuite(s)


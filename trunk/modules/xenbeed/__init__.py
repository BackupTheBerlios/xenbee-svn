"""
	The XenBEE daemon module
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

def TestSuite():
    import unittest, xenbeed.config, xenbeed.staging
    import xenbeed.test_instance

    s = []
    s.append(xenbeed.config.TestSuite())
    s.append(xenbeed.staging.TestSuite())
    s.append(xenbeed.test_instance.suite())
    
    return unittest.TestSuite(s)


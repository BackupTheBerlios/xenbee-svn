#!/usr/bin/python

"""Test cases for the InstanceManager"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"


import unittest, os, sys
from xenbeed.instance import Instance, InstanceManager

class TestInstanceManager(unittest.TestCase):
    def setUp(self):
        self.mgr = InstanceManager()

def suite():
    s1 = unittest.makeSuite(TestInstanceManager, "test")
    return unittest.TestSuite((s1,))

if __name__ == "__main__":
    unittest.main()

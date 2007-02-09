#!/usr/bin/python

"""Test cases for the disk utility functions"""

__version__ = "$Rev$"
__author__ = "$Author$"

import unittest, os, sys, os.path
from xenbeed.disk import makeSparseDisk, makeSwap
from xenbeed.uuid import uuid

class TestDiskFunctions(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join("/tmp", uuid())

    def tearDown(self):
        if os.access(self.path, os.F_OK):
            os.unlink(self.path)

    def test_make_sparse(self):
        self.assertFalse(os.access(self.path, os.F_OK))
        makeSparseDisk(self.path)
        self.assertTrue(os.access(self.path, os.F_OK))

    def test_make_swap(self):
        self.assertFalse(os.access(self.path, os.F_OK))
        makeSwap(self.path)
        self.assertTrue(os.access(self.path, os.F_OK))

def suite():
    s1 = unittest.makeSuite(TestDiskFunctions, "test")
    return unittest.TestSuite((s1,))

if __name__ == "__main__":
    unittest.main()

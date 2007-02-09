#!/usr/bin/python

"""Test cases for the utility functions."""

__version__ = "$Rev$"
__author__ = "$Author$"


import unittest, os
from xenbeed import util
from xenbeed.uuid import uuid

class TestRemoveDirCompletely(unittest.TestCase):
    def setUp(self):
        self.testDir = os.path.join("/tmp", uuid())

    def tearDown(self):
        self.assertFalse(os.access(self.testDir, os.F_OK))

    def test_remove_empty_dir(self):
        """tests the deletion of a directory."""
        self._makeDir(self.testDir)
        self.assertTrue(os.access(self.testDir, os.F_OK))
        util.removeDirCompletely(self.testDir)
        self.assertFalse(os.access(self.testDir, os.F_OK))

    def test_remove_non_empty_dir(self):
        """tests the deletion of a directory tree."""
        subds = [ "dir-%d" % i for i in range(1,10) ]
        files = [ "file-%d" % i for i in xrange(1,10) ]

        for d in subds: self._makeDir(os.path.join(self.testDir, d))
        for f in files: open(os.path.join(self.testDir, f), "wb").write("test")

        self.assertTrue(os.access(self.testDir, os.F_OK))
        for d in subds:
            self.assertTrue(os.access(os.path.join(self.testDir, d), os.F_OK))
        for f in files:
            self.assertTrue(os.access(os.path.join(self.testDir, f), os.F_OK))
        util.removeDirCompletely(self.testDir)
        for d in subds:
            self.assertFalse(os.access(os.path.join(self.testDir, d), os.F_OK))
        for f in files:
            self.assertFalse(os.access(os.path.join(self.testDir, f), os.F_OK))
        self.assertFalse(os.access(self.testDir, os.F_OK))

    def test_remove_deep_dir(self):
        """test the deletion of a deep directory tree."""
        path = self.testDir
        for d in xrange(1,10): path = os.path.join(path, "dir-%d" % d)

        self.assertFalse(os.access(path, os.F_OK))
        self._makeDir(path)
        self.assertTrue(os.access(path, os.F_OK))
        util.removeDirCompletely(self.testDir)
        self.assertFalse(os.access(path, os.F_OK))
        
    def test_remove_non_existent_dir(self):
        nonexistent = os.path.join(self.testDir, "nonexistent")
        self.assertFalse(os.access(nonexistent, os.F_OK))
        util.removeDirCompletely(nonexistent)
        self.assertFalse(os.access(nonexistent, os.F_OK))
        
    def _makeDir(self, d):
        try:
            os.makedirs(d)
        except:
            self.fail("could not create directory: %s" % d)
        

def suite():
    s1 = unittest.makeSuite(TestRemoveDirCompletely, "test")
    return unittest.TestSuite((s1,))

if __name__ == "__main__":
    unittest.main()

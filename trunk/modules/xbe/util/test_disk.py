#!/usr/bin/python

"""Test cases for the disk utility functions"""

__version__ = "$Rev$"
__author__ = "$Author$"

import unittest, os, sys, os.path, tempfile
from xbe.util.disk import makeSparseDisk, makeSwap

class TestDiskFunctions(unittest.TestCase):
    def setUp(self):
        self.path = None

    def tearDown(self):
        if self.path is not None and os.access(self.path, os.F_OK):
            os.unlink(self.path)
            os.close(self.fd)

    def test_make_sparse(self):
        tmp = tempfile.NamedTemporaryFile()
        tmp.seek(0, os.SEEK_END)
        self.assertEquals(0, tmp.tell())
        makeSparseDisk(tmp.name, 2)
        tmp.seek(0, os.SEEK_END)
        self.assertEquals(2*1024**2, tmp.tell())

    def test_make_swap(self):
        tmp = tempfile.NamedTemporaryFile()
        tmp.seek(0, os.SEEK_END)
        self.assertEquals(0, tmp.tell())
        makeSwap(tmp.name, 2)
        tmp.seek(0, os.SEEK_END)
        self.assertEquals(2*1024**2, tmp.tell())

    def test_create_fs(self):
        pass

    def test_mount_image(self):
        pass

def suite():
    s1 = unittest.makeSuite(TestDiskFunctions, "test")
    return unittest.TestSuite((s1,))

if __name__ == "__main__":
    unittest.main()

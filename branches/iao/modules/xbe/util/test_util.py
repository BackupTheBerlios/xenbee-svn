#!/usr/bin/env python

# XenBEE is a software that provides execution of applications
# in self-contained virtual disk images on a remote host featuring
# the Xen hypervisor.
#
# Copyright (C) 2007 Alexander Petry <petry@itwm.fhg.de>.
# This file is part of XenBEE.

# XenBEE is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# XenBEE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA

"""Test cases for the utility functions."""

__version__ = "$Rev: 515 $"
__author__ = "$Author: petry $"


import unittest, os, tempfile
from xbe import util
from xbe.util.uuid import uuid

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

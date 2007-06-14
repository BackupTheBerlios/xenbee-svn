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

"""Test cases for the disk utility functions"""

__version__ = "$Rev$"
__author__ = "$Author$"

import unittest, os, sys, os.path, tempfile
from xbe.util.disk import *

class TestMakeSparse(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_make_sparse(self):
        tmp = tempfile.NamedTemporaryFile()
        tmp.seek(0, os.SEEK_END)
        self.assertEquals(0, tmp.tell())
        makeSparseDisk(tmp.name, 2)
        tmp.seek(0, os.SEEK_END)
        self.assertEquals(2*1024**2, tmp.tell())

class TestMakeSwap(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_make_swap(self):
        tmp = tempfile.NamedTemporaryFile()
        tmp.seek(0, os.SEEK_END)
        self.assertEquals(0, tmp.tell())
        makeSwap(tmp.name, 2)
        tmp.seek(0, os.SEEK_END)
        self.assertEquals(2*1024**2, tmp.tell())

class TestGuessFSType(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_guess_ext2(self):
        tmp = tempfile.NamedTemporaryFile()
        makeImage(tmp.name, FS_EXT2, mega_bytes=16)
        self.assertEqual("ext2", guess_fs_type(tmp.name))
        
    def test_guess_ext3(self):
        tmp = tempfile.NamedTemporaryFile()
        makeImage(tmp.name, FS_EXT3, mega_bytes=16)
        self.assertEqual("ext3", guess_fs_type(tmp.name))

    def test_guess_no_fs(self):
        tmp = tempfile.NamedTemporaryFile()
        try:
            guess = guess_fs_type(tmp.name)
        except ValueError:
            pass
        else:
            self.fail("ValueError expected.")

class TestMakeImage(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_make_image(self):
        tmp = tempfile.NamedTemporaryFile()
        tmp.seek(0, os.SEEK_END)
        self.assertEquals(0, tmp.tell())
        makeImage(tmp.name, FS_EXT2, mega_bytes=2)
        tmp.seek(0, os.SEEK_END)
        self.assertEquals(2*1024**2, tmp.tell())

    def test_make_image_unknown_fs(self):
        tmp = tempfile.NamedTemporaryFile()
        try:
            makeImage(tmp.name, "hopefully_non_existing_fs_type", mega_bytes=2)
        except ProcessError, e:
            pass
        else:
            self.fail("ProcessError expected")
    
    def test_mount_image(self):
        tmp = tempfile.NamedTemporaryFile()
        makeImage(tmp.name, FS_EXT2, mega_bytes=16)
        tmp.seek(0, os.SEEK_END)
        self.assertEquals(16*1024**2, tmp.tell())
        img = mountImage(tmp.name)
        self.assertTrue(img.is_mounted())

    def test_mount_illegal_image(self):
        tmp = tempfile.NamedTemporaryFile()
        try:
            img = mountImage(tmp.name, FS_EXT2)
        except ProcessError:
            pass
        else:
            self.fail("ProcessError expected")

    def test_umount_image(self):
        # check the automatic umounting
        tmp = tempfile.NamedTemporaryFile()
        makeImage(tmp.name, FS_EXT2, mega_bytes=16)
        img = mountImage(tmp.name)
        mount_point = img.mount_point()
        del img
        self.assertTrue(not os.path.exists(mount_point))
        
    def test_write_into_image(self):
        tmp = tempfile.NamedTemporaryFile()
        makeImage(tmp.name, FS_EXT2, mega_bytes=16)
        img = mountImage(tmp.name)
        self.assertTrue(img.is_mounted())
        path = os.path.join(img.mount_point(), "foo")
        open(path, "w").write("hello world!")
        self.assertTrue(os.path.exists(path))
        data = open(path).read()
        self.assertEqual("hello world!", data)

class TestFSTab(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_adding(self):
        fstab = FSTab()
        fstab.add("proc", "/proc", "proc", "defaults", "0", "0")
        
def suite():
    s1 = unittest.makeSuite(TestMakeSparse, "test")
    s2 = unittest.makeSuite(TestMakeSwap, "test")
    s3 = unittest.makeSuite(TestMakeGuessFSType, "test")
    s4 = unittest.makeSuite(TestMakeMakeImage, "test")
    return unittest.TestSuite((s1,s2,s3,s4))

if __name__ == "__main__":
    unittest.main()

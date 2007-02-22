#!/usr/bin/python

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
        
def suite():
    s1 = unittest.makeSuite(TestDiskFunctions, "test")
    return unittest.TestSuite((s1,))

if __name__ == "__main__":
    unittest.main()

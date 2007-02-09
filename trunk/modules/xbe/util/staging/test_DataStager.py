#!/usr/bin/python

"""Test for the DataStager.

TestCase 1: download file and verify it is correct.
	Therefore:

	        1) create temporary file
		2) fill with known content
		3) download the file using the 'file' protocol
		4) verify contents
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

import unittest, os, sys
from xbe.util.staging import DataStager, TempFile

class TestDataStager(unittest.TestCase):
	def setUp(self):
		self.data = "DataStager test case 1"
		self.source = TempFile()
		self.source.write(self.data)
		self.source.flush()

	def test_local_retrieve(self):
		"""Tests whether retrieving a local file works."""
		dst = TempFile()
		stager = DataStager("file://" + self.source.path, dst.path)
		stager.perform(asynchronous=False)
		tmpdata = open(dst.path, "r").read()
		self.assertEqual(self.data, tmpdata)

	def test_remote_retrieve(self):
		remoteSource = "http://www.heise.de/index.html"
		dst = TempFile()
		stager = DataStager(remoteSource, dst.path)
		stager.perform(asynchronous=False)

	def test_local_upload(self):
		"""Tests whether uploading to a local file works."""
		dst = TempFile()
		dstUri = "file://"+dst.path
		stager = DataStager(self.source.path, dstUri)
		stager.perform(asynchronous=False)
		tmpdata = open(dst.path, 'rb').read()
		self.assertEqual(self.data, tmpdata)

class TestTempFile(unittest.TestCase):
	def setUp(self):
		pass

	def test_not_keep(self):
		"""Check if file gets unlinked upon deletion (keep=False)."""
		tmp = TempFile(keep=False)
		path = tmp.path
		self.assertTrue(os.access(path, os.F_OK))
		del tmp
		self.assertFalse(os.access(path, os.F_OK))

	def test_keep(self):
		"""Check if file *does not* get unlinked (keep=True). """
		tmp = TempFile(keep=True)
		path = tmp.path
		self.assertTrue(os.access(path, os.F_OK))
		del tmp
		self.assertTrue(os.access(path, os.F_OK))

		# clean up
		os.unlink(path)

	def test_uniqueness(self):
		"""Make a best practice approach to check uniqueness of temporary files.

		i.e. try to create several temporary files and check
		if their paths are unique.
		
		"""
		tmpfiles = [ TempFile() for i in xrange(20) ]
		tmpfiles.sort(lambda a,b: cmp(a.path, b.path))
		prev_path = None
		for f in tmpfiles:
			self.assertTrue(f.path != prev_path, "two temporary files have the same path!")
			prev_path = f.path
		
def suite():
	s1 = unittest.makeSuite(TestDataStager, 'test')
	s2 = unittest.makeSuite(TestTempFile, 'test')
	return unittest.TestSuite((s1,s2))

if __name__ == '__main__':
	unittest.main()

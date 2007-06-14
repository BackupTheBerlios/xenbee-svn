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

import unittest, os, sys, tempfile
from xbe.util.staging import DataStager

class TestDataStager(unittest.TestCase):
	def setUp(self):
		self.data = "DataStager test case 1"
		self.source_fd, self.source_path = tempfile.mkstemp()
		self.source = os.fdopen(self.source_fd, 'w')
		self.source.write(self.data)
		self.source.flush()

	def tearDown(self):
		# unlink temporary file
		self.source.close()
		os.unlink(self.source_path)

	def test_local_retrieve(self):
		"""Tests whether retrieving a local file works."""
		dst_fd, dst_path = tempfile.mkstemp(text=True)
		stager = DataStager("file://" + self.source_path, dst_path)
		stager.perform(asynchronous=False)
		tmpdata = open(dst_path).read()
		os.unlink(dst_path)
		os.close(dst_fd)
		self.assertEqual(self.data, tmpdata)

	def test_remote_retrieve(self):
		remoteSource = "http://www.heise.de/index.html"
		dst = tempfile.NamedTemporaryFile()
		stager = DataStager(remoteSource, dst.name)
		stager.perform(asynchronous=False)

	def test_local_upload(self):
		"""Tests whether uploading to a local file works."""
		dst = tempfile.NamedTemporaryFile()
		dstUri = "file://"+dst.name
		stager = DataStager(self.source_path, dstUri)
		stager.perform(asynchronous=False)
		tmpdata = dst.read()
		self.assertEqual(self.data, tmpdata)

#class TestTempFile(unittest.TestCase):
#	def setUp(self):
#		pass
#
#	def test_not_keep(self):
#		"""Check if file gets unlinked upon deletion (keep=False)."""
#		tmp = TempFile(keep=False)
#		path = tmp.path
#		self.assertTrue(os.access(path, os.F_OK))
#		del tmp
#		self.assertFalse(os.access(path, os.F_OK))
#
#	def test_keep(self):
#		"""Check if file *does not* get unlinked (keep=True). """
#		tmp = TempFile(keep=True)
#		path = tmp.path
#		self.assertTrue(os.access(path, os.F_OK))
#		del tmp
#		self.assertTrue(os.access(path, os.F_OK))
#
#		# clean up
#		os.unlink(path)
#
#	def test_uniqueness(self):
#		"""Make a best practice approach to check uniqueness of temporary files.
#
#		i.e. try to create several temporary files and check
#		if their paths are unique.
#		
#		"""
#		tmpfiles = [ TempFile() for i in xrange(20) ]
#		tmpfiles.sort(lambda a,b: cmp(a.path, b.path))
#		prev_path = None
#		for f in tmpfiles:
#			self.assertTrue(f.path != prev_path, "two temporary files have the same path!")
#			prev_path = f.path
		
def suite():
	s1 = unittest.makeSuite(TestDataStager, 'test')
	s2 = unittest.makeSuite(TestTempFile, 'test')
	return unittest.TestSuite((s1,s2))

if __name__ == '__main__':
	unittest.main()

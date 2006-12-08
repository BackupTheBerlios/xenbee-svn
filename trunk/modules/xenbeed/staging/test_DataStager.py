"""Test for the DataStager.

TestCase 1: download file and verify it is correct.
	Therefore: 1) create temporary file
                   2) fill with known content
                   3) download the file using the 'file' protocol
                   4) ve
"""

import unittest, os, sys
from DataStager import DataStager
from DataStager import TempFile

class TestDataStager(unittest.TestCase):
	def setUp(self):
		self.data = "DataStager test case 1"
		self.source = TempFile()
		self.source.write(self.data)
		self.source.flush()

	def test_local_retrieve(self):
		dst = TempFile()
		stager = DataStager("file://" + self.source.path, dst.path)
		stager()
		tmpdata = open(dst.path, "r").read()
		self.assertEqual(self.data, tmpdata)

	def test_remote_retrieve(self):
		remoteSource = "http://www.heise.de/index.html"
		dst = TempFile()
		stager = DataStager(remoteSource, dst.path)
		stager.run()

if __name__ == '__main__':
	unittest.main()


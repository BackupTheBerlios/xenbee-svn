#!/usr/bin/python

"""Test cases for the Cache."""

__version__ = "$Rev$"
__author__ = "$Author$"

import os, time
import unittest

from xbe.util.staging.DataStager import TempFile
from xbe.cached import cache
from xbe.util import removeDirCompletely
from xbe.util.uuid import uuid
from twisted.internet import reactor

log = TempFile()
try:
    import xbe.xbed
    xbe.xbed.initLogging(log.path)
except:
    pass

class TestCacheSimple(unittest.TestCase):
    def setUp(self):
        self.cacheDir = "/tmp/cache-test"
        self.cache = cache.Cache(self.cacheDir)
        self.__timeout = 10 # 10 sec timeout

    def tearDown(self):
        removeDirCompletely(self.cacheDir)

    def failed(self, msg=""):
        self.timer.cancel()
        reactor.stop()
        self.fail(msg)

    def test_cache_file(self):
        """tests the caching of a simple file."""
        self.timer = reactor.callLater(self.__timeout, self.failed, "timed out")
        
        tmpFile = TempFile(keep=True)
        self.data = "test data"
        tmpFile.write(self.data)
        tmpFile.flush()

        # cache the file
        def _check(uri):
            from urllib import urlopen
            try:
                cached_data = urlopen(uri).read()
                self.assertEqual(self.data, cached_data)
            except:
                self.fail()
            reactor.stop()
            
        def _cached(fuid):
            os.unlink(tmpFile.path)
            self.cache.lookupByUUID(fuid).addCallback(_check)
        def _failed(err):
            self.fail(err.getErrorMessage())

        self.cache.cache("file://"+tmpFile.path,
                         type="data",
                         description="test data").addCallback(_cached).addErrback(_failed)
        reactor.run()

    
def suite():
    s1 = unittest.makeSuite(TestCacheSimple, "test")
    return unittest.TestSuite((s1,))

if __name__ == "__main__":
    unittest.main()

#!/usr/bin/python

"""Test cases for the Cache."""

__version__ = "$Rev$"
__author__ = "$Author$"

import os, time
import unittest
from xenbeed.staging.DataStager import TempFile
from xenbeed import cache
from xenbeed.util import removeDirCompletely
from xenbeed.uuid import uuid
from twisted.internet import reactor

log = TempFile()
try:
    import xenbeed
    xenbeed.initLogging(log.path)
except:
    pass

class TestCacheSimple(unittest.TestCase):
    def setUp(self):
        self.cacheDir = "/tmp/cache-test"
        self.cache = cache.Cache(self.cacheDir)
        self.__timeout = 10 # 10 sec timeout

    def tearDown(self):
        pass

    def failed(self, msg=""):
        self.timer.cancel()
        reactor.stop()
        self.fail(msg)

    def test_cache_file(self):
        """tests the caching of a simple file."""
        self.timer = reactor.callLater(self.__timeout, self.failed, "timed out")
        
        tmpFile = TempFile(keep=True)
        data = "test data"
        tmpFile.write(data)
        tmpFile.flush()

        # cache the file
        d = self.cache.cache("file://"+tmpFile.path, type="data", description="test data")
        registered_fuid = None

        def _check(fuids):
            global registered_fuid
            self.failUnless(registered_fuid in fuids)
            reactor.stop()
            
        def _cached(fuid):
            global registered_fuid
            registered_fuid = fuid
            os.unlink(tmpFile.path)
            self.cache.lookupType("data").addCallback(_check)
        d.addCallback(_cached)
        reactor.run()
    
def suite():
    s1 = unittest.makeSuite(TestCacheSimple, "test")
    return unittest.TestSuite((s1,))

if __name__ == "__main__":
    unittest.main()

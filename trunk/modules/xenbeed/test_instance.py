#!/usr/bin/python

"""Test cases for the InstanceManager"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"


import unittest, os, sys
from xenbeed.instance import Instance, InstanceManager

class TestInstanceManager(unittest.TestCase):
    def setUp(self):
        self.mgr = InstanceManager()

    def test_new_instance(self):
        """tests the creation of a new instance.

        Does *not* check the creation of a backend instance.

        """
        inst = self.mgr.newInstance()

        # check if the spool directory has been created
        self.assertTrue(os.access(inst.getSpool(), os.F_OK))

        # check that the instance has been registered
        self.assertEqual(inst, self.mgr.lookupByUUID(inst.uuid()))
        self.mgr.removeInstance(inst)
        self.assertEqual(None, self.mgr.lookupByUUID(inst.uuid()))

        self._cleanUp(inst)

    def _cleanUp(self, inst):
        self._removeDirCompletely(inst.getSpool())

    def _removeDirCompletely(self, d):
        for root, dirs, files in os.walk(d):
            for f in files:
                os.unlink(os.path.join(root, f))
            os.rmdir(root)

def suite():
    s1 = unittest.makeSuite(TestInstanceManager, "test")
    return unittest.TestSuite((s1,))

if __name__ == "__main__":
    unittest.main()

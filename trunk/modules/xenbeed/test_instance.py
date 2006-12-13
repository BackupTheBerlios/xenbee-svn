#!/usr/bin/python

"""Test cases for the InstanceManager"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"


import unittest, os, sys
from xenbeed.instance import Instance, InstanceManager
from xenbeed import util

class TestInstanceManager(unittest.TestCase):
    def setUp(self):
        self.mgr = InstanceManager()

    def test_spool_directory(self):
        """tests the creation of a new instance.

        Does *not* check the creation of a backend instance.

        """
        inst = self.mgr.newInstance()

        # check if the spool directory has been created
        self.assertTrue(os.access(inst.getSpool(), os.F_OK))
        self._cleanUp(inst)

    def test_lookup_instance(self):
        """tests the registration of the new instance."""
        # check that the instance has been registered
        inst = self.mgr.newInstance()
        
        self.assertEqual(inst, self.mgr.lookupByUUID(inst.uuid()))
        self._cleanUp(inst)

    def test_remove_instance(self):
        """tests the removal of an instance."""
        
        inst = self.mgr.newInstance()
        self.assertEqual(inst, self.mgr.lookupByUUID(inst.uuid()))
        self.mgr.removeInstance(inst)
        self.assertEqual(None, self.mgr.lookupByUUID(inst.uuid()))
        self._cleanUp(inst)

    def test_successful_instance_creation(self):
        """tests the creation of a backend instance.

        some files are required (will be staged in):
            files = { "image" : "/srv/xen-images/domains/ttylinux/disk.img",
                      "kernel": "/boot/xen0-linux-2.6.17-6-server-xen0",
                      "initrd": "/boot/initrd.img-2.6.17-6-server-xen0" }
        
        """
        # create new instance
        inst = self.mgr.newInstance()

        src_files = { "image" : "/srv/xen-images/domains/ttylinux/disk.img",
                      "kernel": "/srv/xen-images/domains/ttylinux/kernel",
                      "initrd": "/srv/xen-images/domains/ttylinux/initrd" }
        dst_files = {}
        for name, path in src_files.iteritems():
            self.assertTrue(os.access(path, os.F_OK))

            # stage in files
            from xenbeed.staging import DataStager
            dst = os.path.join(inst.getSpool(), name)
            ds = DataStager("file://%s" % path, os.path.join(inst.getSpool(), name))
            ds.run()
            dst_files[name] = dst
        inst.config.setKernel(dst_files["kernel"])
        inst.config.setInitrd(dst_files["initrd"])
        inst.config.addDisk(dst_files["image"], "sda1")

        inst.start()
        state = inst.getBackendState()

        from xenbeed.backend import status
        self.assertTrue(state in (status.BE_INSTANCE_RUNNING, status.BE_INSTANCE_BLOCKED))

        # shut the instance down
        inst.stop()
        self.assertTrue(inst.getBackendState() in (status.BE_INSTANCE_NOSTATE, status.BE_INSTANCE_SHUTOFF))

        inst.cleanUp()

    def _cleanUp(self, inst):
        util.removeDirCompletely(inst.getSpool())

def suite():
    s1 = unittest.makeSuite(TestInstanceManager, "test")
    return unittest.TestSuite((s1,))

if __name__ == "__main__":
    unittest.main()

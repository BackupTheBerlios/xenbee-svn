#!/usr/bin/python

"""Test cases for the InstanceManager"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"


import unittest, os, sys, logging
log = logging.getLogger(__name__)

from xbe.xbed.instance import Instance, InstanceManager
from xbe import util
from xbe.util import disk

class TestInstanceManager(unittest.TestCase):
    def setUp(self):
        self.mgr = InstanceManager()

    def test_spool_directory(self):
        """tests the creation of a new instance.

        Does *not* check the creation of a backend instance.

        """
        log.debug("testing creation of spool directory")
        inst = self.mgr.newInstance()

        # check if the spool directory has been created
        self.assertTrue(os.access(inst.getSpool(), os.F_OK))
        inst.cleanUp()

    def test_lookup_instance(self):
        """tests the registration of the new instance."""
        log.debug("testing instance lookup")
        # check that the instance has been registered
        inst = self.mgr.newInstance()
        
        self.assertEqual(inst, self.mgr.lookupByUUID(inst.uuid()))
        inst.cleanUp()

    def test_remove_instance(self):
        """tests the removal of an instance."""
        log.debug("testing instance removal")

        inst = self.mgr.newInstance()
        self.assertEqual(inst, self.mgr.lookupByUUID(inst.uuid()))
        self.mgr.removeInstance(inst)
        self.assertEqual(None, self.mgr.lookupByUUID(inst.uuid()))
        inst.cleanUp()

    def test_successful_instance_creation(self):
        """tests the creation of a backend instance.

        some files are required (will be staged in):
            files = { "image" : "/srv/xen-images/domains/ttylinux/disk.img",
                      "kernel": "/srv/xen-images/domains/ttylinux/kernel",
                      "initrd": "/srv/xen-images/domains/ttylinux/initrd" }
        
        """
        log.debug("testing instance creation (tiny)")

        # create new instance
        inst = self.mgr.newInstance()

        src_files = { "root" : "/srv/xen-images/domains/ttylinux/disk.img",
                      "kernel": "/srv/xen-images/domains/ttylinux/kernel",
                      "initrd": "/srv/xen-images/domains/ttylinux/initrd" }
        for name, path in src_files.iteritems():
            self.assertTrue(os.access(path, os.F_OK))
            inst.addFile("file://%s" % path, name)

        inst.start()
        state = inst.getBackendState()

        from xbe.xbed.backend import status
        self.assertTrue(state in (status.BE_INSTANCE_RUNNING, status.BE_INSTANCE_BLOCKED))

        # shut the instance down
        inst.stop()
        self.assertTrue(inst.getBackendState() in (status.BE_INSTANCE_NOSTATE, status.BE_INSTANCE_SHUTOFF))

        inst.cleanUp()

    def test_successful_instance_creation_2(self):
        """tests the creation of a backend instance.

        with networking

        some files are required (will be staged in):
            files = { "image" : "/srv/xen-images/domains/xenhobel-1/disk.img",
                      "kernel": "/srv/xen-images/domains/xenhobel-1/kernel",
                      "initrd": "/srv/xen-images/domains/xenhobel-1/initrd" }
        
        """
        log.debug("testing instance creation (big)")

        # create new instance
        inst = self.mgr.newInstance()

        src_files = { "image" : "file:///srv/xen-images/domains/xenhobel-1/disk.img",
                      "kernel": "file:///srv/xen-images/domains/xenhobel-1/kernel",
                      "initrd": "file:///srv/xen-images/domains/xenhobel-1/initrd" }
        inst.addFiles(src_files)
        inst.config.setKernel(inst.getFile("kernel"))
        inst.config.setInitrd(inst.getFile("initrd"))

        # create swap image
        disk.makeSwap(inst.getFile("swap"), 128)

        inst.config.addDisk(inst.getFile("image"), "sda1")
        inst.config.addDisk(inst.getFile("swap"), "sda2")
        inst.config.setMac("00:16:3e:00:00:01")

        inst.start()
        state = inst.getBackendState()

        from xbe.xbed.backend import status
        self.assertTrue(state in (status.BE_INSTANCE_RUNNING, status.BE_INSTANCE_BLOCKED))

        # shut the instance down
        inst.stop()
        self.assertTrue(inst.getBackendState() in (status.BE_INSTANCE_NOSTATE, status.BE_INSTANCE_SHUTOFF))

        inst.cleanUp()

def suite():
    s1 = unittest.makeSuite(TestInstanceManager, "test")
    return unittest.TestSuite((s1,))

if __name__ == "__main__":
    unittest.main()

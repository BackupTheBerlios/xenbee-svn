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

"""Test for the InstanceConfig.

TestCase: set legal mac
TestCase: set illegal mac
"""

__version__ = "$Rev: 515 $"
__author__ = "$Author: petry $"


import unittest, os, sys
from xbe.xbed.config.xen import InstanceConfig, ConfigurationError, LibVirtXMLConfigGenerator

class TestInstanceConfig(unittest.TestCase):
    def setUp(self):
        self.instanceConfig = InstanceConfig("an-instance")

    def test_getName(self):
        self.assertEqual(self.instanceConfig.getInstanceName(), "an-instance")

    def test_set_valid_mac(self):
        """Tests whether a legal mac can be set."""
        mac = "01:02:03:AB:CD:EF"
        self.instanceConfig.setMac(mac)
        self.assertEqual(mac.lower(), self.instanceConfig.getMac())

    def test_set_invalid_mac_1(self):
        """Tests whether an illegal mac can be set.
        using an empty mac
        """
        mac = ""
        try:
            self.instanceConfig.setMac(mac)
        except ConfigurationError:
            pass
        else:
            self.fail("expected a ConfigurationError (invalid mac)")

    def test_set_invalid_mac_2(self):
        """Tests whether an illegal mac can be set.
        using the mac: 0g:02:03:AB:CD:EF
        """
        mac = "0g:02:03:AB:CD:EF"
        try:
            self.instanceConfig.setMac(mac)
        except ConfigurationError:
            pass
        else:
            self.fail("expected a ConfigurationError (invalid mac)")

    def test_set_invalid_mac_3(self):
        """Tests whether a too short mac can be set.
        using the mac: 0a:02
        """
        mac = "0a:02"
        try:
            self.instanceConfig.setMac(mac)
        except ConfigurationError:
            pass
        else:
            self.fail("expected a ConfigurationError (invalid mac)")

    def test_set_invalid_mac_4(self):
        """Tests whether a too long mac can be set (1).
        using the mac: 01:023:03:ab:cd:ef
        """
        mac = "01:023:03:ab:cd:ef"
        try:
            self.instanceConfig.setMac(mac)
        except ConfigurationError:
            pass
        else:
            self.fail("expected a ConfigurationError (invalid mac)")

    def test_set_invalid_mac_5(self):
        """Tests whether a too long mac can be set (2).
        using the mac: 01:02:03:ab:cd:ef:00
        """
        mac = "01:02:03:ab:cd:ef:00"
        try:
            self.instanceConfig.setMac(mac)
        except ConfigurationError:
            pass
        else:
            self.fail("expected a ConfigurationError (invalid mac)")

    def test_default_memory(self):
        """Tests the default memory of 128 MB."""
        self.assertEqual(self.instanceConfig.getMemory(), 128 * 1024**2)

    def test_get_memory_b(self):
        """Tests getMemory() in bytes."""
        expected = 128 * 1024**2
        self.assertEqual(self.instanceConfig.getMemory("b"), expected)

    def test_get_memory_k(self):
        """Tests getMemory() in kilo bytes."""
        expected = 128 * 1024
        self.assertEqual(self.instanceConfig.getMemory("k"), expected)

    def test_get_memory_m(self):
        """Tests getMemory() in mega bytes."""
        expected = 128
        self.assertEqual(self.instanceConfig.getMemory("m"), expected)

    def test_get_memory_g(self):
        """Tests getMemory() in giga bytes."""
        expected = 2
        self.instanceConfig.setMemory( "2G" )
        self.assertEqual(self.instanceConfig.getMemory("g"), expected)

    def test_set_memory_no_modifier(self):
        """Tests whether setting memory without modifier works."""
        expected = 64 * 1024**2
        self.instanceConfig.setMemory(expected)
        self.assertEqual(self.instanceConfig.getMemory(), expected)

        self.instanceConfig.setMemory(str(expected))
        self.assertEqual(self.instanceConfig.getMemory(), expected)

    def test_set_memory_byte_mod(self):
        """Tests whether the byte memory modifier is the same as no modifier."""
        expected = 64 * 1024**2
        self.instanceConfig.setMemory( "%db" % expected )
        self.assertEqual(self.instanceConfig.getMemory(), expected)

    def test_set_memory_kib_mod(self):
        """Tests whether the KB modifier works."""
        expected = 256 * 1024
        self.instanceConfig.setMemory( "256k" )
        self.assertEqual(self.instanceConfig.getMemory(), expected)

    def test_set_memory_meg_mod(self):
        """Tests whether the MB modifier works."""
        expected = 256 * 1024**2
        self.instanceConfig.setMemory( "256m" )
        self.assertEqual(self.instanceConfig.getMemory(), expected)

    def test_set_memory_gig_mod(self):
        """Tests whether the GB modifier works."""
        expected = 2 * 1024**3
        self.instanceConfig.setMemory( "2g" )
        self.assertEqual(self.instanceConfig.getMemory(), expected)

    def test_set_memory_case_mod(self):
        """Tests whether the GB modifier works case insensitive."""
        expected = 2 * 1024**3
        self.instanceConfig.setMemory( "2g" )
        self.assertEqual(self.instanceConfig.getMemory(), expected)
        self.instanceConfig.setMemory( "2G" )
        self.assertEqual(self.instanceConfig.getMemory(), expected)

    def test_add_disk(self):
        """Tests whether a disk can be added."""
        # assert empty
        self.assertTrue(len(self.instanceConfig.getDisks()) == 0)

        # append
        self.instanceConfig.addDisk("/tmp/foobar.img", "sda1")
        # assert not empty
        self.assertFalse(len(self.instanceConfig.getDisks()) == 0)
        disk1 = self.instanceConfig.getDisks()[0]
        self.assertEqual(disk1["path"], "/tmp/foobar.img")
        self.assertEqual(disk1["target"], "sda1")

class TestConfigGenerator(unittest.TestCase):
    """Tests the config generator."""
    
    def setUp(self):
        self.instanceConfig = InstanceConfig("test-config")
        self.instanceConfig.setKernel("/vmlinuz")
        self.instanceConfig.addDisk("/tmp/foo.img", "sda1")
        self.generator = LibVirtXMLConfigGenerator()

    def test_simple_config(self):
        expected = "<?xml version='1.0' encoding='UTF-8'?><domain type='xen'><name>test-config</name><os><type>linux</type><kernel>/vmlinuz</kernel><root>/dev/sda1</root></os><memory>131072</memory><vcpu>1</vcpu><devices><disk type='file'><source file='/tmp/foo.img'/><target dev='sda1'/></disk></devices><on_reboot>restart</on_reboot><on_poweroff>destroy</on_poweroff><on_crash>rename-restart</on_crash></domain>"
        xml = self.generator.generate(self.instanceConfig, pretty=False)
        self.assertEqual(expected, xml)

def suite():
    s1 = unittest.makeSuite(TestInstanceConfig, 'test')
    s2 = unittest.makeSuite(TestConfigGenerator, 'test')
    return unittest.TestSuite((s1,s2))

if __name__ == '__main__':
    unittest.main()


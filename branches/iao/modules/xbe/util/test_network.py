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

"""Test for the network-utility functions."""

__version__ = "$Rev: 515 $"
__author__ = "$Author: petry $"

import unittest, os, sys, socket
from xbe.util import network

class TestDiscoverIPs(unittest.TestCase):
    def setUp(self):
        # listen to some port (ipv4)
        v4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        v4.bind(('127.0.0.1', 0))
        v4.listen(1)
        self.s_ipv4 = v4

        # listen to some port (ipv6)
        if socket.has_ipv6:
            v6 = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            v6.bind(('::1', 0))
            v6.listen(1)
            self.s_ipv6 = v6

        # listen to some port with both families
        self.multi_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.multi_sock.bind(('127.0.0.1', 0))
        self.multi_sock.listen(1)
        if socket.has_ipv6:
            port = self.multi_sock.getsockname()[1]
            self.multi_sock6 = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            self.multi_sock6.bind(('::1', port))
            self.multi_sock6.listen(1)
        
    def tearDown(self):
        del self.s_ipv4
        del self.multi_sock
        if socket.has_ipv6:
            del self.s_ipv6
            del self.multi_sock6

    def test_discover_v4(self):
        peer = self.s_ipv4.getsockname()
        ips = network.discover_ips(peer)
        self.assertTrue("127.0.0.1" in ips)

    def test_discover_v6(self):
        if socket.has_ipv6:
            peer = self.s_ipv6.getsockname()[:2]
            ips = network.discover_ips(peer)
            self.assertTrue("::1" in ips)
        else:
            self.fail("no ipv6 available")

    def test_discover_both(self):
        expected = ["127.0.0.1"]
        if socket.has_ipv6:
            expected.append("::1")
        peer = self.multi_sock.getsockname()[:2]
        ips = network.discover_ips(peer)
        for ip in expected:
            self.assertTrue(ip in ips)

def suite():
    s1 = unittest.makeSuite(TestDiscoverIPs, 'test')
    return unittest.TestSuite(s1)

if __name__ == '__main__':
    unittest.main()

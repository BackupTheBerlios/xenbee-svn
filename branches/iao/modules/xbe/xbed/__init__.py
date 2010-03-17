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

"""
	The XenBEE daemon module
"""

__version__ = "$Rev: 515 $"
__author__ = "$Author: petry $"

def TestSuite():
    import unittest
    import xbe.xbed.config
    import xbe.xbed.test_instance
    import xbe.util.test_util
    import xbe.util.test_disk
    import xbe.util.staging

    s = []
    s.append(xbe.xbed.config.TestSuite())
    s.append(xbe.util.staging.TestSuite())
    s.append(xbe.xbed.test_instance.suite())
    s.append(xbe.util.test_util.suite())
    s.append(xbe.util.test_disk.suite())
    return unittest.TestSuite(s)

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
This module holds possible backends.
"""

__version__ = "$Rev: 515 $"
__author__ = "$Author: petry $"

# backend to use, currently only xen available
_useXen = True
backend = None

def initBackend(backendType="xen"):
    global backend
    if backend:
        raise RuntimeError("backend already initialized!")
    try:
        mod = __import__("xbe.xbed.backend.%s" % backendType, globals(), locals(), ["Backend"])
        backend = mod.Backend()
    except:
        raise

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

"""Generates UUIDs (RFC 4122).

The current implementation uses the uuid command line tool
(debian/ubuntu package 'uuid').
"""

__version__ = "$Rev: 515 $"
__author__ = "$Author: petry $"

import commands
class UUID:
    def __init__(self, random=True):
        """Initializes the UUID generator.

        If random is True, truly random (version 4) UUIDs are generated.
        Non random UUIDs are based on time and the local node (version 1).
        """
        self.random = random
        if self.random:
            self.cmd = "uuid -v 4"
        else:
            self.cmd = "uuid -v 1"

        import commands
        (status, uuid) = commands.getstatusoutput(self.cmd)
        if status != 0:
            self.cmd = "uuidgen"

    def next(self):
        """Returns the next UUID."""
        (status, uuid)  = commands.getstatusoutput(self.cmd)
        if status != 0:
            raise RuntimeError(
                "could get UUID: probably the command '%s' could not be run" % (self.cmd))
        return uuid.lower()

    def __call__(self):
        """same as next()"""
        return self.next()

__UUID = UUID()
def uuid():
    return __UUID.next()

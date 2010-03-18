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
Common exceptions.
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

from pprint import pformat

class XenBeeException(Exception):
    def __str__(self):
        return "<%(cls)s - %(msg)s: %(args)s>" % {
            "cls": self.__class__.__name__,
            "msg": str(self.message),
            "args": pformat(self.args),
        }
    __repr__ = __str__

class BackendException(XenBeeException):
    def __init__(self, msg, inst_id, *args):
        XenBeeException.__init__(self, msg, inst_id, *args)
        self.inst_id = inst_id

class InstanceCreationError(BackendException):
    pass

class DomainLookupError(BackendException):
    pass

class SecurityError(XenBeeException):
    pass


from subprocess import CalledProcessError
class ProcessError(CalledProcessError):
    def __init__(self, returncode, cmd, stderr, stdout):
        CalledProcessError.__init__(self, returncode, cmd)
        self.stderr = stderr
        self.stdout = stdout

    def __str__(self):
        s = CalledProcessError.__str__(self)
        s += ": %s" % (self.stderr)
        return s

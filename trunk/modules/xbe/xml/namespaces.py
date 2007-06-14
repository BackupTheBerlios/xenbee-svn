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
Several important namespaces
"""

__version__ = "$Rev$"
__author__ = "$Author$"

# taken from http://effbot.org/zone/element-lib.htm
# and added the __str__ method, which returns the uri
#
class NS(object):
    def __init__(self, uri):
        self.__uri = uri
    def __getattr__(self, tag):
        return "{%s}%s" % (self.__uri, tag)
    def __call__(self, path):
        return "/".join([getattr(self, tag) for tag in path.split("/")])
    def __str__(self):
        return self.__uri
    def __repr__(self):
        return self.__class__.__name__ + "('%s')" % str(self)

def decodeTag(tag):
    if tag[0] == '{':
        return tag[1:].split("}", 1)
    else:
        return None, tag


XBE_NS  = "http://www.example.com/schemas/xbe/2007/01/xbe"
XBE_SEC_NS  = "http://www.example.com/schemas/xbe/2007/01/xbe-sec"
XSDL_NS = "http://www.example.com/schemas/xbe/2007/01/xsdl"
JSDL_NS = "http://schemas.ggf.org/jsdl/2005/11/jsdl"
JSDL_POSIX_NS = "http://schemas.ggf.org/jsdl/2005/11/jsdl-posix"
DSIG_NS = "http://www.w3.org/2000/09/xmldsig#"
OGSA_BES_ACTIVITY_NS = "http://schemas.ggf.org/bes/2006/08/bes-activity"
CALANA_STATE_NS = "http://www.example.com/schemas/calana/2007/01/calana_state"
XSD_NS = "http://www.w3.org/2001/XMLSchema"

XSD = NS(XSD_NS)
XBE  = NS(XBE_NS)
XSDL = NS(XSDL_NS)
JSDL = NS(JSDL_NS)
JSDL_POSIX = NS(JSDL_POSIX_NS)
DSIG = NS(DSIG_NS)
XBE_SEC = NS(XBE_SEC_NS)
BES_ACTIVITY=NS(OGSA_BES_ACTIVITY_NS)
CALANA_STATE = NS(CALANA_STATE_NS)

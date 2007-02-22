#!/usr/bin/env python
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
        return tag[1:].split("}")
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

XBE  = NS(XBE_NS)
XSDL = NS(XSDL_NS)
JSDL = NS(JSDL_NS)
JSDL_POSIX = NS(JSDL_POSIX_NS)
DSIG = NS(DSIG_NS)
XBE_SEC = NS(XBE_SEC_NS)
BES_ACTIVITY=NS(OGSA_BES_ACTIVITY_NS)
CALANA_STATE = NS(CALANA_STATE_NS)

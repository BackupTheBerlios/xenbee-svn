"""
This module holds possible backends.
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

# backend to use, currently only xen available
_useXen = True
if _useXen:
    from xenbeed.backend.xen import *
else:
    from xenbeed.backend.local import *


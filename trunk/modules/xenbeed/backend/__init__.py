"""
This module holds possible backends.
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

# backend to use, currently only xen available
from xenbeed.backend.xen import *

"""
This module holds possible backends.
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

# backend to use, currently only xen available
_useXen = True
backend = None

def initBackend(backendType="xen"):
    global backend
    if backend:
        raise RuntimeError("backend already initialized!")
    try:
        mod = __import__("xenbeed.backend.%s" % backendType, globals(), locals(), ["Backend"])
        backend = mod.Backend()
    except:
        raise

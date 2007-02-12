"""
Common exceptions.
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"


class XenBeeException(Exception):
    pass

class BackendException(XenBeeException):
    def __init__(self, msg, err=None):
        XenBeeException.__init__(self, msg)
        self.err = err

class InstanceCreationError(BackendException):
    pass

class SecurityError(XenBeeException):
    pass


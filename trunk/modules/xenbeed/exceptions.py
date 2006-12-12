"""
Common exceptions.
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"


class XenBeeException(Exception):
    pass

class BackendException(XenBeeException):
    pass

class InstanceCreationError(BackendException):
    pass

class SecurityError(XenBeeException):
    pass


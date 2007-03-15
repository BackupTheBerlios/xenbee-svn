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

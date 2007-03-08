"""
Common exceptions.
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

class XenBeeException(Exception):
    pass

class BackendException(XenBeeException):
    def __init__(self, msg, inst_id, *args):
        XenBeeException.__init__(self, msg, *args)
        self.inst_id = inst_id

class InstanceCreationError(BackendException):
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

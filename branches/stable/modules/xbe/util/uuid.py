"""Generates UUIDs (RFC 4122).

The current implementation uses the uuid command line tool
(debian/ubuntu package 'uuid').
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

import commands
class UUID:
    def __init__(self, random=True):
        """Initializes the UUID generator.

        If random is True, truly random (version 4) UUIDs are generated.
        Non random UUIDs are based on time and the local node (version 1).
        """
        self.random = random
        if self.random:
            self.cmd = "uuid -v 4"
        else:
            self.cmd = "uuid -v 1"

        import commands
        (status, uuid) = commands.getstatusoutput(self.cmd)
        if status != 0:
            self.cmd = "uuidgen"

    def next(self):
        """Returns the next UUID."""
        (status, uuid)  = commands.getstatusoutput(self.cmd)
        if status != 0:
            raise RuntimeError(
                "could get UUID: probably the command '%s' could not be run" % (self.cmd))
        return uuid.lower()

    def __call__(self):
        """same as next()"""
        return self.next()

__UUID = UUID()
def uuid():
    return __UUID.next()

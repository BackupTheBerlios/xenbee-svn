"""
The Xen backend.
"""

import commands
import os
from xenbeed.backend import errors

__all__ = [ "createInstance" ]

def _runcmd(cmd, arg):
    return commands.getstatusoutput("xm %s %s" % (cmd, arg))

def createInstance(path_to_config):
    # check if file exists
    if not os.access(path_to_config, os.R_OK):
        return (errors.E_CONFIG, "config does not exist")
    (status, output) = _runcmd("dry-run", path_to_config)
    if status != 0:
        return (errors.E_CREAT, "dry-run failed: %s" % output)
    (status, output) = _runcmd("create", path_to_config)
    if status != 0:
        return (errors.E_CREAT, "create failed: %s" % output)
    return (0, "")

"""
The Xen backend.
"""

__version__ = "$Rev: $"
__author__ = "$Author$"

import commands
import os, os.path, re
from traceback import format_exc as format_exception
from twisted.python import log

from xenbeed.config.xen import XenConfigGenerator
from xenbeed.backend import errors
from xenbeed.exceptions import *

__all__ = [ "createInstance", "retrieveID", "shutdownInstance", "destroyInstance" ]

def _runcmd(cmd, *args):
    """Executes the specified command on the xen backend, using 'xm'.

    WARNING: this function is exploitable using an injection mechanism
    
    TODO: find a way to escape correctly (re.escape includes
    double-backslashes not only for quotes)
    """
#    cmdline = "xm " + "'%s' " % re.escape(cmd) + " ".join(map(lambda x: "'%s'" % re.escape(str(x)), args))
    cmdline = "xm " + "'%s' " % cmd + " ".join(map(lambda x: "'%s'" % x, args))
    return commands.getstatusoutput(cmdline)

def retrieveID(inst):
    """Retrieves the backend id for the given instance."""
    (status, output) = _runcmd("domid", inst.config.getInstanceName())
    if status == 0:
        return int(output)
    else:
        return -1
    
def createInstance(inst):
    """Creates a new backend-instance.

    inst - an instance object (created by the InstanceManager)
    """

    # check if another (or maybe this) instance is running with same name
    # (that should not happen!)
    if retrieveID(inst) >= 0:
        log.err("backend: another instance (or maybe this one?) is already known to xen")
        raise InstanceCreaionError("instance already known")

    # build configuration
    generator = XenConfigGenerator() # TODO: create factory for 'backend'
    try:
        cfg = generator.generate(inst.config)
    except:
        log.err("backend: could not generate config: " + format_exception())
        raise
    
    # write current config to inst.spool/config
    try:
        cfg_path = os.path.join(inst.getSpool(), inst.uuid())
        cfg_file = open(cfg_path, "w")
        cfg_file.write(cfg)
        cfg_file.close()
    except:
        log.err("backend: could not write current config: %s" % format_exception())
        raise

    # dry-run and create instance
    (status, output) = _runcmd("dry-run", cfg_path)
    if status != 0:
        log.err("backend: could not execute dry-run: %s" % output)
        raise InstanceCreaionError("dry-run failed: %s" % output)

    # TODO: decouple it using a thread/spawn whatever
    (status, output) = _runcmd("create", path_to_config)
    if status != 0:
        log.err("backend: could not create backend instance: %s" % output)
        raise InstanceCreaionError("create failed: %s" % output)

    inst.backend_id = retrieveID(inst)
    return inst.backend_id

def destroyInstance(inst):
    """Attempts to destroy the backend instance immediately.

    WARNING: the instance will be shutdown, so any programs running
             within the instance will be killed(!). From the xm
             man-page: it is equivalent to ripping the power cord.
    """
    (status, output) = _runcmd("destroy", inst.backend_id)
    if status != 0:
        log.err("backend: could not destroy backend instance: %s" % output)
        raise BackendException("destroy failed: %s" % output)

def shutdownInstance(inst):
    """Attempts to cleanly shut the backend instance down."""
    (status, output) = _runcmd("shutdown", inst.backend_id)
    if status != 0:
        log.err("backend: could not shutdown backend instance: %s" % output)
        raise BackendException("destroy failed: %s" % output)

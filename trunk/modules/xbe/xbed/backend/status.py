# XenBEE is a software that provides execution of applications
# in self-contained virtual disk images on a remote host featuring
# the Xen hypervisor.
#
# Copyright (C) 2007 Alexander Petry <petry@itwm.fhg.de>.
# This file is part of XenBEE.

# XenBEE is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# XenBEE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA

"""Status codes for backend instances.

BE_INSTANCE_NOSTATE = 0    # unknown or no state
BE_INSTANCE_RUNNING = 1    # obviously the instance is running
BE_INSTANCE_BLOCKED = 2    # the instance blocked due to some I/O (may mean that is simply waits at the loginprompt)
BE_INSTANCE_PAUSED = 3     # instance has been paused by the user
BE_INSTANCE_SHUTDOWN = 4   # the instance is going to be shutdown
BE_INSTANCE_SHUTOFF = 5    # the instance has been shut off
BE_INSTANCE_CRASHED = 6    # the instance has crashed

"""

__version__ = "$Rev$"
__author__ = "$Author$"

BE_INSTANCE_NOSTATE = 0    # unknown or no state
BE_INSTANCE_RUNNING = 1    # obviously the instance is running
BE_INSTANCE_BLOCKED = 2    # the instance blocked due to some I/O (may mean that is simply waits at the loginprompt)
BE_INSTANCE_PAUSED = 3     # instance has been paused by the user
BE_INSTANCE_SHUTDOWN = 4   # the instance is going to be shutdown
BE_INSTANCE_SHUTOFF = 5    # the instance has been shut off
BE_INSTANCE_CRASHED = 6    # the instance has crashed

def getStateName(state):
    return states.get(state, states[BE_INSTANCE_NOSTATE])

states = {
    BE_INSTANCE_NOSTATE: "NOSTATE",
    BE_INSTANCE_RUNNING: "RUNNING",
    BE_INSTANCE_BLOCKED: "BLOCKED",
    BE_INSTANCE_PAUSED: "PAUSED",
    BE_INSTANCE_SHUTDOWN: "SHUTDOWN",
    BE_INSTANCE_SHUTOFF: "SHUTOFF",
    BE_INSTANCE_CRASHED: "CRASHED",
    None: "NOSTATE",
    "NOSTATE": BE_INSTANCE_NOSTATE,
    "RUNNING": BE_INSTANCE_RUNNING,
    "BLOCKED": BE_INSTANCE_BLOCKED,
    "PAUSED" : BE_INSTANCE_PAUSED,
    "SHUTDOWN": BE_INSTANCE_SHUTDOWN,
    "SHUTOFF": BE_INSTANCE_SHUTOFF,
    "CRASHED": BE_INSTANCE_CRASHED
    }

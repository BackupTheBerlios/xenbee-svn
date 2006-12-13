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
    return _names.get(state, _names[BE_INSTANCE_NOSTATE])

_names = { BE_INSTANCE_NOSTATE: "NOSTATE",
           BE_INSTANCE_RUNNING: "RUNNING",
           BE_INSTANCE_BLOCKED: "BLOCKED",
           BE_INSTANCE_PAUSED: "PAUSED",
           BE_INSTANCE_SHUTDOWN: "SHUTDOWN",
           BE_INSTANCE_SHUTOFF: "SHUTOFF",
           BE_INSTANCE_CRASHED: "CRASHED",
           None: "NOSTATE" }

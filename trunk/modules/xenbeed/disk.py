"""Functions usefull to create disk images.

   sparse disks, swap space

"""

import commands, os

def makeSparseDisk(path, mega_bytes=128):
    """Creates a sparse.

    path -- the path where to generate the file.
    mega_bytes -- as the name says, the number of mega bytes.

    requires: dd
    
    """
    if os.access(path, os.F_OK):
        raise RuntimeError("could not create sparse disk: file '%s' does already exist.")
    if not os.access("/dev/zero", os.R_OK):
        raise RuntimeError("sorry, but I need /dev/zero to operate.")
    try:
        mega_bytes = int(mega_bytes)
    except:
        raise
    status, out = commands.getstatusoutput("/bin/dd if=/dev/zero of='%s' bs=1024k count=1 seek=%d" % (path, mega_bytes))
    if status != 0:
        raise RuntimeError("could not run 'dd': %d: %s" % (status, out))
    if not os.access(path, os.F_OK):
        raise RuntimeError("after making sparse disk the image does not exist!")

def makeSwap(path, mega_bytes=128):
    """Create a swap disk.

    Uses the makeSparseDisk to create a sparse disk of size
    'mega_bytes' at path and running 'mkswap' on it.

    requires: mkswap

    """
    makeSparseDisk(path, mega_bytes)
    status, out = commands.getstatusoutput("/sbin/mkswap '%s'" % path)
    if status != 0:
        raise RuntimeError("could not run 'mkswap': %d: %s" % (status, out))

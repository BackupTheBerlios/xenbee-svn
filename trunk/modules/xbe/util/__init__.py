"""Utility functions used at several points in this project.

Provides:
    removeDirCompletely: same as 'rm -rf <dir>'
"""

import os
import threading

def removeDirCompletely(d):
    for root, dirs, files in os.walk(d):
        map(os.unlink, [os.path.join(root,f) for f in files])
        map(removeDirCompletely, [os.path.join(root, subdir) for subdir in dirs])
        os.rmdir(root)

try:
    os.statvfs
except AttributeError, ae:
    # no implementation provided
    # implement Win32 interface here
    pass
else:
    # taken from: http://mail.python.org/pipermail/python-dev/2001-March/013783.html
    import statvfs
    def freespace(path):
        """ freespace(path) -> integer
        
        Return the number of bytes available to the user on the file
        system pointed to by path."""
        s = os.statvfs(path)
        return s[statvfs.F_BAVAIL] * long(s[statvfs.F_BSIZE])

    def totalspace(path):
        """ totalspace(path) -> integer

        Return the total number of bytes the file system pointed to by
        path has."""
        s = os.statvfs(path)
        return s[statvfs.F_BLOCKS] * long(s[statvfs.F_BSIZE])

class Lock:
    counter = 0
    def __init__(self, name=None, reentrant=True):
        if reentrant:
            self.__mtx = threading.RLock()
        else:
            self.__mtx = threading.Lock()
        self.__name = name or "Lock-%d" % (Lock.counter, )
        Lock.counter += 1

    def acquire(self):
        self.log("acquiring %s" % (self.__name))
        self.__mtx.acquire()
        self.log("acquired %s" % (self.__name))

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


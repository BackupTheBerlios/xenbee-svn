#!/usr/bin/env python

import os, sys, pwd

if len(sys.argv) < 3:
    print >>sys.stderr, "usage:", sys.argv[0], "user newroot [command [args...]]"
    sys.exit(1)

user, root = sys.argv[1:3]

try:
    uid = int(user)
except ValueError:
    try:
        uid = pwd.getpwnam(user).pw_uid
    except KeyError:
        print >>sys.stderr, "no such user:", user
        sys.exit(2)

argv = sys.argv[3:]
if not len(argv):
    argv = [os.environ.get("SHELL", "/bin/sh")]

os.chroot(root)
os.chdir('/')
os.setuid(uid)
os.execl(*argv)

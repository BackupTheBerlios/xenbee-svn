#!/usr/bin/env python

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

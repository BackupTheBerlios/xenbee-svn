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

"""A class that represents a UserDatabase against which one may check certificates."""

import sys, os, os.path, threading, logging, signal
log = logging.getLogger(__name__)

from xbe.util.singleton import Singleton
from xbe.xml.security import Subject

from twisted.internet import task

class User:
    def __init__(self, subject):
        self.__subject = subject

    def __repr__(self):
        return "<%(cls)s Subject=%(subj)s>" % {
            "cls": self.__class__.__name__,
            "subj": repr(self.subject())
        }

    def subject(self):
        return self.__subject

    def matches(self, certificate):
        if certificate is None:
            raise ValueError("certificate must not be None")
        return self.subject() == certificate.subject()

class UserDatabase(Singleton):
    def __init__(self, path):
        Singleton.__init__(self)
        self.mtx = threading.RLock()
        self.__user_db = path
        self.__users = []
        self.__mtime = 0
        self.rebuilder = task.LoopingCall(self.rebuild)
        self.rebuilder.start(10)

    def __read_file(self):
        users = []
        for line in open(self.__user_db).readlines():
            line = line.split("#", 1)[0].strip()
            if len(line):
                users.append(User(Subject(line)))
        return users

    def rebuild(self, force=False):
        self.mtx.acquire()
        try:
            newUsers = None
            if force:
                newUsers = self.__read_file()
            else:
                mtime = os.path.getmtime(self.__user_db)
                if mtime > self.__mtime:
                    newUsers = self.__read_file()
                    self.__mtime = mtime
            if newUsers is not None:
                newUsers.sort()
                if newUsers != self.__users:
                    self.__users = newUsers
        	    log.debug("rebuilt user database from file %s: %d user(s) allowed", self.__user_db, len(newUsers))
        except Exception, e:
            log.warn("could not rebuild user database: %s", str(e))
        finally:
            self.mtx.release()

    def check_x509(self, cert):
        self.mtx.acquire()
        try:
            for user in self.__users:
                if user.matches(cert):
                    return True
        except Exception, e:
            log.debug("user %s failed authentication check: %s", str(cert.subject()), str(e))
        finally:
            self.mtx.release()
        return False


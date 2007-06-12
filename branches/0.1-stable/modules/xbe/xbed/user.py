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
        self.__mtime = 0
        self.rebuilder = task.LoopingCall(self.rebuild)
        self.rebuilder.start(10)

    def __read_file(self):
        users = []
        for line in open(self.__user_db).readlines():
            line = line.split("#", 1)[0].strip()
            if len(line):
                users.append(User(Subject(line)))
        log.debug("rebuilt user database: %d user(s) allowed", len(users))
        self.__users = users

    def rebuild(self, force=False):
        self.mtx.acquire()
        try:
            if force:
                self.__read_file()
            else:
                mtime = os.path.getmtime(self.__user_db)
                if mtime > self.__mtime:
                    self.__read_file()
                    self.__mtime = mtime
        finally:
            self.mtx.release()

    def check_x509(self, cert):
        self.mtx.acquire()
        try:
            for user in self.__users:
                if user.matches(cert):
                    return True
        finally:
            self.mtx.release()
        return False

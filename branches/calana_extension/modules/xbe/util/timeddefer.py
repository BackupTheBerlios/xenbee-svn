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

"""A Deferred, that has a timeout associated."""


from twisted.internet import defer
from twisted.python import failure

class TimeoutError(Exception):
    pass

def timeout(deferred):
    deferred.errback(failure.Failure(TimeoutError("the Deferred timed out"))

class TimedDeferred(defer.Deferred):
    def __init__(self):
        defer.Deferred.__init__(self)

    def setTimeout(self, secs, timeoutFunc=timeout, *args, **kw):
        """overrides the timeout handling in defer.Deferred.
        returns an id, that can be used to cancel the timeout.
        """
        if self.called:
            return
        if self.timeoutCall:
            raise RuntimeError("Do not set a timeout twice!")

        from twisted.internet import reactor
        self.timeoutCall = reactor.callLater(
            secs,
            lambda: self.called or timeoutFunc(self, *args, **kw))
        return self.timeoutCall

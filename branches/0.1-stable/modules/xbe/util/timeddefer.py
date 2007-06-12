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

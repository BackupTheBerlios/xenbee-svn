"""I encapsulate activities.

   * IActivity the interface all activities have to implement
   * IComplexActivity represents an activity that consists of other
     (smaller) activities
"""

from zope.interface import Interface, implements
import threading

class IActivity(Interface):
    """I represent a single activity."""

    def start(on_finish=None, *args, **kw):
        """start the activity"""
    def cleanup():
        """run clean up code, if any"""
    def abort():
        """abort the activity"""
    def startable():
        """is the activity startable"""
    def finished():
        """did the activity already finish"""
    def failed():
        """did the activity fail"""
    def aborted():
        """has the activity been aborted"""
    def done():
        """returns true if either finshed, failed or aborted returns true"""
    def getResult():
        """return the result of the activity"""

class IComplexActivity(IActivity):
    """I represent a more complex activity, that consists of other activities"""
    def add(activity):
        """add an activity to this one."""
    def join():
        """joins the execution of the activity."""

class ActivityAborted(Exception):
    """An activity may raise this, if it has been aborted."""
    pass

class SimpleActivity:
    implements(IActivity)

    activity_func = None
    
    def __init__(self, func=None, args=(), kw={}):
        self.__started = False
        self.__failed = False
        self.__finished = False
        self.__aborted = False
        self.__result = None
        self.__mtx = threading.RLock()
        if func is not None:
            self.activity_func = func
            self.activity_funcArgs = args
            self.activity_funcKwArgs = kw
            
    def __repr__(self):
        try:
            self.__mtx.acquire()
            rv = "<%(cls)s" % {
                "cls": self.__class__.__name__
            }
            if self.__started:
                rv += " started"
            if self.__finished:
                rv += " finished"
            if self.__aborted:
                rv += " aborted"
            if self.__result is not None:
                rv += " with %r" % (self.__result)
            rv += ">"
        finally:
            self.__mtx.release()
        return rv

    def run(self):
        """The default function that gets executed if none has been
        given to the constructor.

        You may override this in subclasses.
        """
        if self.activity_func is not None:
            return self.activity_func(*self.activity_funcArgs,
                                      **self.activity_funcKwArgs)
        else:
            return None
        
    def startable(self):
        self.__mtx.acquire()
        rv = not self.__started
        self.__mtx.release()
        return rv

    def failed(self):
        self.__mtx.acquire()
        rv = self.__failed
        self.__mtx.release()
        return rv

    def finished(self):
        self.__mtx.acquire()
        rv = self.__finished
        self.__mtx.release()
        return rv

    def abort(self):
        self.__mtx.acquire()
        self.__aborted = True
        self.__mtx.release()

    def aborted(self):
        self.__mtx.acquire()
        rv = self.__aborted
        self.__mtx.release()
        return rv

    def done(self):
        self.__mtx.acquire()
        rv = self.__finished or self.__failed or self.__aborted
        self.__mtx.release()
        return rv

    def getResult(self):
        self.__mtx.acquire()
        rv = self.__result
        self.__mtx.release()
        return rv

    def start(self, on_finish=None, args=(), kw={}):
        try:
            self.__mtx.acquire()
            if not self.startable():
                raise RuntimeError("already started")
            self.__started = True
            self.__aborted = False
            self.__failed = False
            self.__finished = False

            rv = None
            try:
                try:
                    self.__mtx.release()
                    rv = self.run()
                finally:
                    self.__mtx.acquire()
            except Exception, e:
                self.__result = e
                self.__failed = True
            else:
                self.__finished = True
                self.__result = rv
            self.__started = False
        finally:
            self.__mtx.release()
            
        if on_finish is not None:
            try:
                on_finish(*args, **kw)
            except:
                pass

    def cleanup(self):
        pass

class _ThreadContext:
    check_abort = None

    def __init__(self):
        self.__aborted = False

    def set_aborted(self):
        self.__aborted = True

    def aborted(self):
        return self.__aborted

class ActivityProxy:
    def __call__(self, context, *args, **kw):
        pass
    
    def abort(self):
        pass

class ThreadedActivity:
    implements(IActivity)
    
    def __init__(self, proxy, args=(), kw={}):
        self.__started = False
        self.__failed = False
        self.__finished = False
        self.__aborted = False
        self.__do_abort = False
        self.__result = None
        self.__mtx = threading.RLock()
        if proxy is None:
            raise ValueError("proxy must not be None")
        
        if not callable(proxy):
            raise ValueError("proxy must be callable", proxy)
        if not hasattr(proxy, 'abort') and not callable(proxy.abort):
            raise ValueError("proxy must provide 'abort' method")
        self.proxy = proxy
        self.proxyArgs = args
        self.proxyKwArgs = kw
            
    def __repr__(self):
        try:
            self.__mtx.acquire()
            rv = "<%(cls)s" % {
                "cls": self.__class__.__name__
            }
            if self.__started:
                rv += " started"
            if self.__finished:
                rv += " finished"
            if self.__aborted:
                rv += " aborted"
            if self.__result is not None:
                rv += " with %r" % (self.__result)
            rv += ">"
        finally:
            self.__mtx.release()
        return rv

    def startable(self):
        self.__mtx.acquire()
        rv = not self.__started
        self.__mtx.release()
        return rv

    def failed(self):
        self.__mtx.acquire()
        rv = self.__failed
        self.__mtx.release()
        return rv

    def finished(self):
        self.__mtx.acquire()
        rv = self.__finished
        self.__mtx.release()
        return rv

    def abort(self):
        try:
            self.__mtx.acquire()
            self.__do_abort = True
            if self.__started:
                try:
                    self.proxy.abort()
                except:
                    pass
#                try:
#                    self.__mtx.release()
#                    self.join()
#                finally:
#                    self.__mtx.acquire()
        finally:
            self.__mtx.release()

    def check_abort(self):
        self.__mtx.acquire()
        rv = self.__do_abort
        self.__mtx.release()
        return rv

    def aborted(self):
        self.__mtx.acquire()
        rv = self.__aborted
        self.__mtx.release()
        return rv

    def done(self):
        self.__mtx.acquire()
        rv = self.__finished or self.__failed or self.__aborted
        self.__mtx.release()
        return rv

    def getResult(self):
        self.__mtx.acquire()
        rv = self.__result
        self.__mtx.release()
        return rv

    def start(self, on_finish=None, args=(), kw={}):
        try:
            self.__mtx.acquire()
            if not self.startable():
                raise RuntimeError("already started")
            if self.check_abort():
                # already aborted
                self.__do_abort = False
                self.__aborted = True
                return
            
            self.__started = True
            self.__aborted = False
            self.__failed = False
            self.__finished = False

            argv = [on_finish]
            argv.append(args)
            self.__worker = threading.Thread(target=self.__thread_body,
                                             args=argv, kwargs=kw)
            self.__worker.start()
        finally:
            self.__mtx.release()

    def join(self):
        try:
            self.__mtx.acquire()
            try:
                t = self.__worker
            except AttributeError:
                pass
            else:
                self.__mtx.release()
                t.join()
                self.__mtx.acquire()
        finally:
            self.__mtx.release()

    def __thread_body(self, on_finish=None, args=(), kw={}):
        ctxt = _ThreadContext()
        ctxt.check_abort = self.check_abort
        try:
            rv = self.proxy(ctxt, *self.proxyArgs, **self.proxyKwArgs)
        except ActivityAborted, e:
            try:
                self.__mtx.acquire()
                self.__aborted = True
                self.__do_abort = False
            finally:
                self.__mtx.release()
        except Exception, e:
            try:
                self.__mtx.acquire()
                self.__failed = True
                self.__result = e
            finally:
                self.__mtx.release()
        else:
            try:
                self.__mtx.acquire()
                self.__result = rv
                if ctxt.aborted() or self.check_abort():
                    self.__aborted = True
                    self.__do_abort = False
                else:
                    self.__finished = True
            except Exception, e:
                self.__result = e
                self.__failed = True
            finally:
                self.__mtx.release()
        try:
            self.__mtx.acquire()
            del self.__worker
        finally:
            self.__mtx.release()

        if on_finish is not None:
            try:
                on_finish(*args, **kw)
            except:
                pass
            
    def cleanup(self):
        pass

class ComplexActivity:
    """I am a complex activity.

    On starting, i spawn a thread that loops over all my activities.
    """
    implements(IComplexActivity)

    def __init__(self, activities=[]):
        self.__mtx = threading.RLock()

        # let our worker wait on a condition as long as an activity is
        # running
        self.__cv = threading.Condition(self.__mtx)

        self.__activities = []
        self.__current = None
        self.__started = False
        self.__failed = False
        self.__finished = False
        self.__do_abort = False
        self.__aborted = False
        self.__result = None
        
        self.add_many(activities)

    def __add(self, act):
        if not IActivity.providedBy(act):
            raise ValueError("activity is required to implement IActivity", act)
        self.__activities.append(act)
        
    def add(self, act):
        if not self.startable():
            raise RuntimeError("cannot add activity while started")
        try:
            self.__mtx.acquire()
            self.__add(act)
        finally:
            self.__mtx.release()
        return self
        
    def add_many(self, activities):
        if not self.startable():
            raise RuntimeError("cannot add activities while started")
        try:
            self.__mtx.acquire()
            map(self.__add, activities)
        finally:
            self.__mtx.release()
            
    def startable(self):
        self.__mtx.acquire()
        rv = not self.__started
        self.__mtx.release()
        return rv

    def finished(self):
        self.__mtx.acquire()
        rv = self.__finished
        self.__mtx.release()
        return rv

    def failed(self):
        self.__mtx.acquire()
        rv = self.__failed
        self.__mtx.release()
        return rv

    def aborted(self):
        self.__mtx.acquire()
        rv = self.__aborted
        self.__mtx.release()
        return rv

    def done(self):
        self.__mtx.acquire()
        rv = self.__finished or self.__failed or self.__aborted
        self.__mtx.release()
        return rv

    def abort(self):
        self.__mtx.acquire()
        # just mark the request, that we want to abort
        self.__do_abort = True
        if self.__current is not None:
            self.__current.abort()
        self.__mtx.release()

    def getResult(self):
        self.__mtx.acquire()
        rv = self.__result
        self.__mtx.release()
        return rv

    def start(self, on_finish=None, args=(), kw={}):
        try:
            self.__mtx.acquire()
            if not self.startable():
                raise RuntimeError("already started")
            self.__started = True
            argv = [on_finish]
            argv.append(args)
            self.__worker = threading.Thread(target=self.__thread_body,
                                             args=argv, kwargs=kw)
            self.__worker.start()
        finally:
            self.__mtx.release()

    def join(self):
        try:
            self.__mtx.acquire()
            try:
                t = self.__worker
            except AttributeError:
                pass
            else:
                self.__mtx.release()
                try:
                    t.join()
                finally:
                    self.__mtx.acquire()
        finally:
            self.__mtx.release()

    def __thread_body(self, on_finish=None, args=(), kw={}):
        md = threading.local()  # my local data
        md.current = None
        
        # a function that wakes me up
        def notify_me():
            self.__cv.acquire()
            self.__cv.notify()
            self.__cv.release()
        
        # as long as there are activities, start one after the other
        self.__cv.acquire()
        while len(self.__activities) and not self.done():
            if self.__current is None:
                self.__current = self.__activities.pop(0)
                try:
                    self.__cv.release()
                    try:
                        self.__current.start(on_finish=notify_me)
                    except Exception, e:
                        self.__mtx.acquire()
                        self.__failed = True
                        self.__result = e
                        self.__mtx.release()
                        continue
                finally:
                    self.__cv.acquire()
            while not self.__current.done():
                try:
                    self.__cv.wait()
                except Exception, e:
                    pass
                if self.__do_abort:
                    self.__current.abort()
                    self.__do_abort = False
            if self.__do_abort:
                self.__current.abort()
                self.__do_abort = False

            # the activity has finished, check its state
            if self.__current.aborted():
                self.__aborted = True
                self.__result = self.__current.getResult()
                break
            if self.__current.finished():
                self.__result = self.__current.getResult()
                self.__current = None
                continue
            if self.__current.failed():
                self.__failed = True
                self.__result = self.__current.getResult()
                break
        self.__started = False

        if not self.__failed and not self.__aborted:
            self.__finished = True
        del self.__worker
        self.__cv.release()

        if on_finish is not None:
            try:
                on_finish(*args, **kw)
            except:
                pass

    def __repr__(self):
        try:
            self.__mtx.acquire()
            rv = "<%(cls)s" % {
                "cls": self.__class__.__name__
            }
            if self.__started:
                rv += " started"
                rv += " (%d remaining)" % (len(self.__activities))
            if self.__finished:
                rv += " finished"
            if self.__aborted:
                rv += " aborted"
            if self.__failed:
                rv += " failed"
            if self.__result is not None:
                rv += " with %r" % (self.__result)
            rv += ">"
        finally:
            self.__mtx.release()
        return rv

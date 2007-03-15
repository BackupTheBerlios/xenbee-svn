"""Implements the Observer pattern."""

class Observable:
    def __init__(self):
        self.__observers = []

    def addObserver(self, observer, *args, **kw):
        if not callable(observer):
            raise ValueError("observer must be callable", observer)
        self.__observers.append( (observer, args, kw) )

    def removeObserver(self, observer):
        for o_tuple in self.__observers:
            if o_tuple[0] == observer:
                self.__obserservers.remove(o_tuple)
                return
        raise LookupError("no such observer", observer)

    def notify(self, arg):
        for o, args, kw in self.__observers:
            o(arg, *args, **kw)

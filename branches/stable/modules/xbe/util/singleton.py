"""Represents a singleton from the Singleton-Pattern."""

class Singleton:
    _instance = None

    def __init__(self):
        pass

    def getInstance(cls, *args, **kw):
        if cls._instance is None:
            cls._instance = cls(*args, **kw)
        return cls._instance
    getInstance = classmethod(getInstance)

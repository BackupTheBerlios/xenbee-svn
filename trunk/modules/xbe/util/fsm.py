#!/usr/bin/env python
"""
A Finite State Machine
"""

__version__ = "$Rev: 50 $"
__author__ = "$Author: petry $"

import logging, threading
log = logging.getLogger(__name__)

class FSMException(Exception):
    pass

class FSMError(FSMException):
    pass
class NoTransition(FSMError):
    pass

class State(object):
    def __init__(self, name):
        self.name = name

class FSM(object):
    def __init__(self, start=None):
        self.__inTransition = False
        self.__mtx = threading.RLock()
        self.__states = {}
        self.transitions = []
        self.current = None
        if start != None:
            self.newState(start)
            self.setStartState(start)
        else:
            self.start = None

    def newState(self, name):
        try:
            self.__mtx.acquire()
            if name in self.__states.keys():
                raise FSMError("state `%s' does already exist." % name)
            s = State(name)
            self.__states[name] = s
        finally:
            self.__mtx.release()
        return s

    def states(self):
        return self.__states.keys()

    def setStartState(self, name):
        self.__mtx.acquire()
        self.start = self.getState(name)
        self.reset()
        self.__mtx.release()

    def getState(self, name):
        return self.__states[name]

    def reset(self):
        self.__mtx.acquire()
        self.current = self.start
        self.__mtx.release()

    def addTransition(self, s0, s1, input_symbol, output, *args, **kw):
        try:
            self.__mtx.acquire()
            try:
                stateS0 = self.getState(s0)
                stateS1 = self.getState(s1)
            except KeyError, ke:
                raise FSMError("no such state", ke.args[0])

            t = self.__getTransition(stateS0, input_symbol)
            if t:
                raise FSMError("a transition for that symbol already exists: %s => %s"
                               % (stateS0.name, t[0].name))

            self.transitions.append( (stateS0,
                                      stateS1,
                                      input_symbol,
                                      output,
                                      args,
                                      kw) )
        finally:
            self.__mtx.release()

    def __getTransition(self, state, input_symbol):
        for s0, s1, i, o, args, kw in self.transitions:
            if s0 != state: continue
            if i != input_symbol: continue
            return (s1, o, args, kw)

    def consume(self, symbol, *extra_args, **extra_kw):
        try:
            self.__mtx.acquire()

            if not self.start or not self.current:
                raise FSMError("neither start state nor current state available!")

            assert not self.__inTransition, "already in some transition"
            self.__inTransition = True
            
            if callable(symbol):
                i = symbol()
            else:
                i = symbol
            t = self.__getTransition(self.current, i)
            if not t:
                raise NoTransition("no transition", self.current.name, i)
            s1, o, args, kw = t
            args = [ a for a in args ]
            args.extend(extra_args)
            kw.update(extra_kw)
            if o:
                # call transition method
                rv = o(*args, **kw)
            self.__inTransition = False
            self.current = s1
        finally:
            self.__mtx.release()
        return rv

    def getCurrentState(self):
        return self.current.name

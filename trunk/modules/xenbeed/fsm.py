#!/usr/bin/env python
"""
A Finite State Machine
"""

__version__ = "$Rev: 50 $"
__author__ = "$Author: petry $"

import logging
log = logging.getLogger(__name__)

class FSMException(Exception):
    pass

class FSMError(FSMException):
    pass

class State(object):
    def __init__(self, name):
        self.name = name

class FSM(object):
    def __init__(self, start=None):
        self.states = {}
        self.transitions = []
        self.current = None
        if start != None:
            self.newState(start)
            self.setStartState(start)
        else:
            self.start = None

    def newState(self, name):
        if name in self.states.keys():
            raise FSMError("state `%s' does already exist." % name)
        s = State(name)
        self.states[name] = s
        return s

    def setStartState(self, name):
        self.start = self.getState(name)
        self.reset()

    def getState(self, name):
        return self.states[name]

    def reset(self):
        self.current = self.start

    def addTransition(self, s0, s1, input_symbol, output, *args, **kw):
        try:
            stateS0 = self.getState(s0)
            stateS1 = self.getState(s1)
        except KeyError, ke:
            raise FSMError("no such state `%s'" % ke.args[0])

        t = self.getTransition(stateS0, input_symbol)
        if t:
            raise FSMError("a transition for that symbol already exists: %s => %s" % (stateS0.name, t[0].name))

        self.transitions.append( (stateS0,
                                  stateS1,
                                  input_symbol,
                                  output,
                                  args,
                                  kw) )

    def getTransition(self, state, input_symbol):
        for s0, s1, i, o, args, kw in self.transitions:
            if s0 != state: continue
            if i != input_symbol: continue
            return (s1, o, args, kw)

    def consume(self, symbol, *extra_args, **extra_kw):
        if not self.start or not self.current:
            raise FSMError("neither start state nor current state available!")
        
        if callable(symbol):
            i = symbol()
        else:
            i = symbol
        t = self.getTransition(self.current, i)
        if not t:
            raise FSMError("no transition from `%s' for input symbol `%s'" % (self.current.name, i))
        s1, o, args, kw = t
        args = [ a for a in args ]
        args.extend(extra_args)
        kw.update(extra_kw)
        if o:
            # call transition method
            o(*args, **kw)
        self.current = s1
        return self.current

    def getCurrentState(self):
        return self.current.name

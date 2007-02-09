#!/usr/bin/python

"""Test cases for the FSM"""

__version__ = "$Rev: 14 $"
__author__ = "$Author: petry $"

import unittest
from xenbeed.fsm import FSM, FSMError

class TestFSM(unittest.TestCase):
    def setUp(self):
        self.fsm = FSM("0")
        self.fsm.newState("1")
        self.fsm.addTransition("0", "0", "0", self.zeroIgnored)
        self.fsm.addTransition("0", "1", "1", self.oneSeen)
        self.fsm.addTransition("1", "1", "1", self.oneIgnored)
        self.fsm.addTransition("1", "0", "0", self.zeroSeen)

    def zeroSeen(self):
        pass
    def zeroIgnored(self):
        pass
    def oneSeen(self):
        pass
    def oneIgnored(self):
        pass

    def test_add_indeterministic_transition(self):
        try:
            self.fsm.addTransition("0", "0", "0", None)
        except FSMError, e:
            pass
        else:
            self.fail("expected FSMError (indeterministic transition)")

    def test_illegal_input(self):
        try:
            self.fsm.consume("2")
        except FSMError, e:
            pass
        else:
            self.fail("expected FSMError (no transition)")

    def test_consume_0(self):
        self.assertEqual(self.fsm.getCurrentState(), "0")
        self.fsm.consume("0")
        self.assertEqual(self.fsm.getCurrentState(), "0")

    def test_consume_1(self):
        self.assertEqual(self.fsm.getCurrentState(), "0")
        self.fsm.consume("1")
        self.assertEqual(self.fsm.getCurrentState(), "1")

    def test_consume_010(self):
        self.assertEqual(self.fsm.getCurrentState(), "0")
        self.fsm.consume("0")
        self.assertEqual(self.fsm.getCurrentState(), "0")
        self.fsm.consume("1")
        self.assertEqual(self.fsm.getCurrentState(), "1")
        self.fsm.consume("0")
        self.assertEqual(self.fsm.getCurrentState(), "0")

    def test_consume_011(self):
        self.assertEqual(self.fsm.getCurrentState(), "0")
        self.fsm.consume("0")
        self.assertEqual(self.fsm.getCurrentState(), "0")
        self.fsm.consume("1")
        self.assertEqual(self.fsm.getCurrentState(), "1")
        self.fsm.consume("1")
        self.assertEqual(self.fsm.getCurrentState(), "1")

    def test_consume_add_arg(self):
        fsm = FSM()
        fsm.newState("A")
        fsm.newState("B")
        fsm.setStartState("A")

        def _test(*args):
            self.assertEqual(args[-1], "test")
        fsm.addTransition("A", "B", "input1", _test, "foo")
        fsm.consume("input1", "test")

def suite():
    s1 = unittest.makeSuite(TestFSM, "test")
    return unittest.TestSuite((s1,))

if __name__ == "__main__":
    unittest.main()

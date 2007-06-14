#!/usr/bin/env python

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

"""Test cases for the FSM"""

__version__ = "$Rev: 14 $"
__author__ = "$Author: petry $"

import unittest
from xbe.util.fsm import FSM, FSMError

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

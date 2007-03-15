#!/usr/bin/python

"""Test for the bes module."""

__version__ = "$Rev$"
__author__ = "$Author$"

import unittest, os, sys
from xbe.xml import bes
from lxml import etree
from xbe.xml.namespaces import *

class TestFromXBETaskState(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_legal_Pending_no_substate(self):
        state = "Pending"
        bes_elem = bes.fromXBETaskState(state)
        self.assertEqual(bes_elem.attrib["state"], state)
    def test_legal_Running_no_substate(self):
        state = "Running"
        bes_elem = bes.fromXBETaskState(state)
        self.assertEqual(bes_elem.attrib["state"], state)
    def test_legal_Failed_no_substate(self):
        state = "Failed"
        bes_elem = bes.fromXBETaskState(state)
        self.assertEqual(bes_elem.attrib["state"], state)
    def test_legal_Terminated_no_substate(self):
        state = "Terminated"
        bes_elem = bes.fromXBETaskState(state)
        self.assertEqual(bes_elem.attrib["state"], state)
    def test_legal_Finished_no_substate(self):
        state = "Finished"
        bes_elem = bes.fromXBETaskState(state)
        self.assertEqual(bes_elem.attrib["state"], state)

    def test_illegal_bes_state_no_substate(self):
        state = "IllegalBESState"
        try:
            bes_elem = bes.fromXBETaskState(state)
        except ValueError:
            pass
        else:
            self.fail("ValueError expected, invalid bes-state: %s" % state)

    def test_legal_with_calana_substate(self):
        main_state = "Pending"
        sub_state = "Reserved"
        state = ":".join((main_state,sub_state))
        bes_elem = bes.fromXBETaskState(state)
        self.assertEqual(bes_elem.attrib["state"], main_state)
        self.assertEqual(len(bes_elem), 1)
        self.assertEqual(bes_elem[0].tag, CALANA_STATE("Reserved"))

    def test_legal_with_xbe_substate(self):
        main_state = "Running"
        sub_state = "Instance-Starting"
        state = ":".join((main_state,sub_state))
        bes_elem = bes.fromXBETaskState(state)
        self.assertEqual(bes_elem.attrib["state"], main_state)
        self.assertEqual(len(bes_elem), 1)
        self.assertEqual(bes_elem[0].tag, XBE("Instance-Starting"))

class TestToXBETaskState(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass
    def test_legal_pending_no_substate(self):
        xml = """
        <bes:ActivityStatus xmlns:bes="http://schemas.ggf.org/bes/2006/08/bes-activity"
                            state="Pending"/>"""
        bes_elem = etree.fromstring(xml)
        state = bes.toXBETaskState(bes_elem)
        self.assertEqual(state, "Pending")

    def test_illegal_bes_state(self):
        xml = """
        <bes:ActivityStatus xmlns:bes="http://schemas.ggf.org/bes/2006/08/bes-activity"
                            state="IllegalBESState"/>"""
        try:
            bes_elem = etree.fromstring(xml)
            bes.toXBETaskState(bes_elem)
        except ValueError:
            pass
        else:
            self.fail("ValueError expected, illegal bes state")

    def test_legal_with_xbe_substate(self):
        xml = """
        <bes:ActivityStatus xmlns:bes="http://schemas.ggf.org/bes/2006/08/bes-activity" state="Running">
           <ns0:Instance-Starting xmlns:ns0="http://www.example.com/schemas/xbe/2007/01/xbe"/>
        </bes:ActivityStatus>
        """
        bes_elem = etree.fromstring(xml)
        state = bes.toXBETaskState(bes_elem)
        self.assertEqual(state, "Running:Instance-Starting")
        
def suite():
    s1 = unittest.makeSuite(TestFromXBETaskState, 'test')
    s2 = unittest.makeSuite(TestToXBETaskState, 'test')
    return unittest.TestSuite((s1,s2))

if __name__ == '__main__':
    unittest.main()

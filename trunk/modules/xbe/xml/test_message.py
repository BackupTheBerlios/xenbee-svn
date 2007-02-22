#!/usr/bin/python

"""Test for the Message module."""

__version__ = "$Rev$"
__author__ = "$Author$"

import unittest, os, sys
from xbe.xml import message, errcode, bes
from lxml import etree
from xbe.xml.namespaces import *

class TestServerMessages(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_Error_as_xml(self):
        msg = message.Error(errcode.OK, "additional message")
        xml = msg.as_xml()
        elem = xml.find(XBE("MessageBody")+"/"+msg.tag)
        self.assertNotEqual(elem, None)
        self.assertEqual(int(elem.attrib[XBE("code")]), errcode.OK)
        self.assertEqual(elem.findtext(XBE("Description")), errcode.info[errcode.OK][1])
        self.assertEqual(elem.findtext(XBE("Message")), "additional message")

    def test_Error_from_xml(self):
        xml = """<xbe:Message xmlns:xbe="http://www.example.com/schemas/xbe/2007/01/xbe"><xbe:MessageHeader/><xbe:MessageBody><xbe:Error xbe:code="200"><xbe:Name>OK</xbe:Name><xbe:Description>everything ok</xbe:Description><xbe:Message>additional message</xbe:Message></xbe:Error></xbe:MessageBody></xbe:Message>"""
        msg = message.MessageBuilder.from_xml(etree.fromstring(xml))
        self.assertTrue(isinstance(msg, message.Error))
        self.assertEqual(msg.code(), errcode.OK)
        self.assertEqual(msg.message(), "additional message")

    def test_CacheEntries_as_xml(self):
        msg = message.CacheEntries()
        msg.add(uri="http://www.example.com/entry/1",
                hash="01234",
                type="data",
                description="example description 1")
        msg.add(uri="http://www.example.com/entry/2",
                hash="43210",
                type="image",
                description="example description 2")
        xml = msg.as_xml()
        elem = xml.find(XBE("MessageBody")+"/"+msg.tag)
        self.assertNotEqual(elem, None)
        entry1, entry2 = elem.findall(XBE("Entry"))
        self.assertNotEqual(entry1, None)
        self.assertNotEqual(entry2, None)

        self.assertEqual(entry1.findtext(XBE.URI), "http://www.example.com/entry/1")
        self.assertEqual(entry1.findtext(XBE.HashValue), "01234")
        self.assertEqual(entry1.findtext(XBE.Type), "data")
        self.assertEqual(entry1.findtext(XBE.Description), "example description 1")
        
        self.assertEqual(entry2.findtext(XBE.URI), "http://www.example.com/entry/2")
        self.assertEqual(entry2.findtext(XBE.HashValue), "43210")
        self.assertEqual(entry2.findtext(XBE.Type), "image")
        self.assertEqual(entry2.findtext(XBE.Description), "example description 2")

    def test_CacheEntries_from_xml(self):
        xml = """
        <xbe:Message xmlns:xbe="http://www.example.com/schemas/xbe/2007/01/xbe">
           <xbe:MessageHeader/>
              <xbe:MessageBody>
                <xbe:CacheEntries>
                  <xbe:Entry>
                   <xbe:HashValue>01234</xbe:HashValue>
                   <xbe:Type>data</xbe:Type>
                   <xbe:URI>http://www.example.com/entry/1</xbe:URI>
                   <xbe:Description>example description 1</xbe:Description>
                  </xbe:Entry>
                  <xbe:Entry>
                   <xbe:HashValue>43210</xbe:HashValue>
                   <xbe:Type>image</xbe:Type>
                   <xbe:URI>http://www.example.com/entry/2</xbe:URI>
                   <xbe:Description>example description 2</xbe:Description>
                  </xbe:Entry>
                </xbe:CacheEntries>
            </xbe:MessageBody>
        </xbe:Message>"""
        msg = message.MessageBuilder.from_xml(xml)
        self.assertTrue(isinstance(msg, message.CacheEntries))
        entry1, entry2 = msg.entries()
        
        self.assertEqual(len(entry1.keys()), 4)
        self.assertEqual(len(entry2.keys()), 4)
        
        self.assertEqual(entry1["URI"], "http://www.example.com/entry/1")
        self.assertEqual(entry1["HashValue"], "01234")
        self.assertEqual(entry1["Type"], "data")
        self.assertEqual(entry1["Description"], "example description 1")

        self.assertEqual(entry2["URI"], "http://www.example.com/entry/2")
        self.assertEqual(entry2["HashValue"], "43210")
        self.assertEqual(entry2["Type"], "image")
        self.assertEqual(entry2["Description"], "example description 2")

    def test_StatusList_as_xml(self):
        msg = message.StatusList()
        msg.add(id="task-1", submitted_tstamp=1171983221, state="Pending")
        xml = msg.as_xml()
        elem = xml.find(XBE("MessageBody")+"/"+msg.tag)
        self.assertNotEqual(elem, None)
        self.assertEqual(elem.findtext(XBE("Status/TaskID")), "task-1")
        self.assertEqual(int(elem.findtext(XBE("Status/Submitted"))), 1171983221)
        state = bes.toXBETaskState(elem.find(XBE("Status/State"))[0])
        self.assertEqual(state, "Pending")

    def test_StatusList_from_xml(self):
        xml = """
        <xbe:Message xmlns:xbe="http://www.example.com/schemas/xbe/2007/01/xbe">
           <xbe:MessageHeader/>
           <xbe:MessageBody>
             <xbe:StatusList>
               <xbe:Status>
                 <xbe:Submitted>1171983221</xbe:Submitted>
                 <xbe:TaskID>task-1</xbe:TaskID>
                 <xbe:State>
                   <bes:ActivityStatus xmlns:bes="http://schemas.ggf.org/bes/2006/08/bes-activity"
                                       state="Pending"/>
                 </xbe:State>
               </xbe:Status>
             </xbe:StatusList>
           </xbe:MessageBody>
        </xbe:Message>
        """
        msg = message.MessageBuilder.from_xml(etree.fromstring(xml))
        self.assertTrue(isinstance(msg, message.StatusList))
        (entry,) = msg.entries()
        self.assertEqual(entry["TaskID"], "task-1")
        self.assertEqual(entry["Submitted"], "1171983221")
        self.assertEqual(entry["State"], "Pending")

class TestInstanceMessages(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_InstanceAvailable_as_xml(self):
        msg = message.InstanceAvailable('test-instance-id')
        msg.add_ip("127.0.0.1")
        xml = msg.as_xml()

        elem = xml.find(XBE("MessageBody")+"/"+msg.tag)
        elem = xml.find(XBE("MessageBody/InstanceAvailable"))
        self.assertNotEqual(elem, None)
        self.assertEqual(elem.attrib[XBE("inst-id")], "test-instance-id")

        ip = elem.findtext(XBE("NodeInformation/Network/IPList/IP"))
        self.assertEqual(ip, "127.0.0.1")

    def test_InstanceAvailable_from_xml(self):
        xml = """
        <xbe:Message xmlns:xbe="http://www.example.com/schemas/xbe/2007/01/xbe">
          <xbe:MessageHeader/>
          <xbe:MessageBody>
            <xbe:InstanceAvailable xbe:inst-id="test-instance-id">
              <xbe:NodeInformation>
                <xbe:Network>
                  <xbe:IPList>
                    <xbe:IP>127.0.0.1</xbe:IP>
                  </xbe:IPList>
                </xbe:Network>
              </xbe:NodeInformation>
            </xbe:InstanceAvailable>
          </xbe:MessageBody>
        </xbe:Message>"""
        msg = message.MessageBuilder.from_xml(etree.fromstring(xml))
        self.assertTrue(isinstance(msg, message.InstanceAvailable))
        self.assertEqual(msg.ips(), ["127.0.0.1"])
        self.assertEqual(msg.inst_id(), "test-instance-id")
        
    def test_TaskFinished_as_xml(self):
        msg = message.TaskFinished(inst_id="instance 1", exitcode=1, task_id="task 2")
        xml = msg.as_xml()
        elem = xml.find(XBE("MessageBody")+"/"+msg.tag)
        self.assertNotEqual(elem, None)
        self.assertEqual(elem.attrib.get(XBE("inst-id")), "instance 1")
        self.assertEqual(elem.attrib.get(XBE("task-id")), "task 2")
        self.assertEqual(int(elem.findtext(XBE("ExitCode"))), 1)

    def test_TaskFinished_from_xml(self):
        xml = """
        <xbe:Message xmlns:xbe="http://www.example.com/schemas/xbe/2007/01/xbe">
          <xbe:MessageHeader/>
          <xbe:MessageBody>
            <xbe:TaskFinished xbe:inst-id="instance 1" xbe:task-id="task 2">
               <xbe:ExitCode>1</xbe:ExitCode>
            </xbe:TaskFinished>
          </xbe:MessageBody>
        </xbe:Message>
        """
        msg = message.MessageBuilder.from_xml(xml)
        self.assertTrue(isinstance(msg, message.TaskFinished))
        self.assertEqual(msg.task_id(), "task 2")
        self.assertEqual(msg.inst_id(), "instance 1")
        self.assertEqual(msg.exitcode(), 1)

    def test_InstanceAlive_as_xml(self):
        msg = message.InstanceAlive(inst_id="instance 1", uptime=1171983221)
        xml = msg.as_xml()
        elem = xml.find(XBE("MessageBody")+"/"+msg.tag)
        self.assertNotEqual(elem, None)
        self.assertEqual(elem.attrib.get(XBE("inst-id")), "instance 1")
        self.assertEqual(int(elem.findtext(XBE("Uptime"))), 1171983221)

    def test_InstanceAlive_from_xml(self):
        xml = """
        <xbe:Message xmlns:xbe="http://www.example.com/schemas/xbe/2007/01/xbe">
          <xbe:MessageHeader/>
          <xbe:MessageBody>
            <xbe:InstanceAlive xbe:inst-id="instance 1">
              <xbe:Uptime>1171983221</xbe:Uptime>
            </xbe:InstanceAlive>
          </xbe:MessageBody>
        </xbe:Message>
        """
        msg = message.MessageBuilder.from_xml(xml)
        self.assertTrue(isinstance(msg, message.InstanceAlive))
        self.assertEqual(msg.inst_id(), "instance 1")
        self.assertEqual(msg.uptime(), 1171983221)

class TestClientMessages(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_CertificateRequest_as_xml(self):
        msg = message.CertificateRequest()
        xml = msg.as_xml()
        elem = xml.find(XBE("MessageBody")+"/"+msg.tag)
        self.assertNotEqual(elem, None)

    def test_CertificateRequest_from_xml(self):
        xml = """<xbe:Message xmlns:xbe="http://www.example.com/schemas/xbe/2007/01/xbe"><xbe:MessageHeader/><xbe:MessageBody><xbe:CertificateRequest/></xbe:MessageBody></xbe:Message>"""
        msg = message.MessageBuilder.from_xml(xml)
        self.assertTrue(isinstance(msg, message.CertificateRequest))

    def test_ListCache_as_xml(self):
        msg = message.ListCache()
        xml = msg.as_xml()
        elem = xml.find(XBE("MessageBody")+"/"+msg.tag)
        self.assertNotEqual(elem, None)

    def test_ListCache_from_xml(self):
        xml = """<xbe:Message xmlns:xbe="http://www.example.com/schemas/xbe/2007/01/xbe"><xbe:MessageHeader/><xbe:MessageBody><xbe:ListCache/></xbe:MessageBody></xbe:Message>"""
        msg = message.MessageBuilder.from_xml(xml)
        self.assertTrue(isinstance(msg, message.ListCache))

    def test_Kill_as_xml(self):
        msg = message.Kill("task 1", signal=15)
        xml = msg.as_xml()
        elem = xml.find(XBE("MessageBody")+"/"+msg.tag)
        self.assertNotEqual(elem, None)

        self.assertEqual(int(elem.attrib[XBE("signal")]), 15)
        self.assertEqual(elem.findtext(XBE("Task")), "task 1")

    def test_Kill_from_xml(self):
        xml = """
        <xbe:Message xmlns:xbe="http://www.example.com/schemas/xbe/2007/01/xbe">
          <xbe:MessageHeader/>
          <xbe:MessageBody>
            <xbe:Kill xbe:signal="15">
              <xbe:Task>task 2</xbe:Task>
            </xbe:Kill>
          </xbe:MessageBody>
        </xbe:Message>"""
        msg = message.MessageBuilder.from_xml(etree.fromstring(xml))
        self.assertTrue(isinstance(msg, message.Kill))
        self.assertEqual(msg.signal(), 15)
        self.assertEqual(msg.task_id(), "task 2")

    def test_Kill_illegal_signals(self):
        try:
            message.Kill("task 1", signal="a")
        except ValueError:
            pass
        else:
            self.fail("expected a ValueError, since signal 'a' is illegal")

    def test_StatusRequest_as_xml(self):
        msg = message.StatusRequest("task 1")
        xml = msg.as_xml()
        elem = xml.find(XBE("MessageBody")+"/"+msg.tag)
        self.assertNotEqual(elem, None)
        self.assertEqual(elem.attrib[XBE("task-id")], "task 1")

    def test_StatusRequest_as_xml_no_task_id(self):
        msg = message.StatusRequest()
        xml = msg.as_xml()
        elem = xml.find(XBE("MessageBody")+"/"+msg.tag)
        self.assertNotEqual(elem, None)
        self.assertEqual(elem.attrib.get(XBE("task-id")), None)

    def test_StatusRequest_from_xml(self):
        xml = """<xbe:Message xmlns:xbe="http://www.example.com/schemas/xbe/2007/01/xbe"><xbe:MessageHeader/><xbe:MessageBody><xbe:StatusRequest xbe:task-id="task-1"/></xbe:MessageBody></xbe:Message>"""
        msg = message.MessageBuilder.from_xml(xml)
        self.assertTrue(isinstance(msg, message.StatusRequest))
        self.assertEqual(msg.task_id(), "task-1")

    def test_StatusRequest_from_xml_no_task_id(self):
        xml = """<xbe:Message xmlns:xbe="http://www.example.com/schemas/xbe/2007/01/xbe"><xbe:MessageHeader/><xbe:MessageBody><xbe:StatusRequest/></xbe:MessageBody></xbe:Message>"""
        msg = message.MessageBuilder.from_xml(xml)
        self.assertTrue(isinstance(msg, message.StatusRequest))
        self.assertEqual(msg.task_id(), None)

def suite():
    s1 = unittest.makeSuite(TestServerMessages, 'test')
    s2 = unittest.makeSuite(TestInstanceMessages, 'test')
    s3 = unittest.makeSuite(TestClientMessages, 'test')
    return unittest.TestSuite((s1,s2,s3))

if __name__ == '__main__':
    unittest.main()

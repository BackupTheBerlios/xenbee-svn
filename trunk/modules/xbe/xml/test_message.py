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
        self.assertEqual(int(elem.attrib["code"]), errcode.OK)
        self.assertEqual(elem.findtext(XBE("Description")), errcode.info[errcode.OK][1])
        self.assertEqual(elem.findtext(XBE("Message")), "additional message")

    def test_Error_from_xml(self):
        xml = """<xbe:Message xmlns:xbe="http://www.example.com/schemas/xbe/2007/01/xbe"><xbe:MessageHeader/><xbe:MessageBody><xbe:Error code="200"><xbe:Name>OK</xbe:Name><xbe:Description>everything ok</xbe:Description><xbe:Message>additional message</xbe:Message></xbe:Error></xbe:MessageBody></xbe:Message>"""
        msg = message.MessageBuilder.from_xml(etree.fromstring(xml))
        self.assertTrue(isinstance(msg, message.Error))
        self.assertEqual(msg.code(), errcode.OK)
        self.assertEqual(msg.message(), "additional message")

    def test_CacheEntries_as_xml(self):
        msg = message.CacheEntries()
        msg.add(uri="http://www.example.com/entry/1",
                meta={ "hash": "01234",
                       "type": "data",
                       "description": "example description 1", })
        
        msg.add(uri="http://www.example.com/entry/2",
                meta={ "hash": "43210",
                       "type": "image",
                       "description": "example description 2",})
        xml = msg.as_xml()
        elem = xml.find(XBE("MessageBody")+"/"+msg.tag)
        self.assertNotEqual(elem, None)

        entries = elem.findall(XBE("Entry"))
        self.assertTrue(len(entries) == 2)

        entries.sort(lambda a,b: cmp(a.findtext(XBE.URI), b.findtext(XBE.URI)))
        entry1, entry2 = entries

        self.assertEqual(entry1.findtext(XBE.URI), "http://www.example.com/entry/1")
        self.assertEqual(entry2.findtext(XBE.URI), "http://www.example.com/entry/2")

    def test_CacheEntries_from_xml(self):
        xml = """
        <xbe:Message xmlns:xbe="http://www.example.com/schemas/xbe/2007/01/xbe">
           <xbe:MessageHeader/>
              <xbe:MessageBody>
                <xbe:CacheEntries>
                  <xbe:Entry>
                    <xbe:URI>http://www.example.com/entry/1</xbe:URI>
                    <xbe:Meta>
                      <xbe:Dict>
                         <xbe:Entry key="hash">01234</xbe:Entry>
                         <xbe:Entry key="type">data</xbe:Entry>
                         <xbe:Entry key="description">example description 1</xbe:Entry>
                      </xbe:Dict>   
                    </xbe:Meta>
                  </xbe:Entry>
                </xbe:CacheEntries>
            </xbe:MessageBody>
        </xbe:Message>"""
        msg = message.MessageBuilder.from_xml(xml)
        self.assertTrue(isinstance(msg, message.CacheEntries))
        entries = msg.entries()
        self.assertEqual(entries.keys()[0], "http://www.example.com/entry/1")
        entry1 = entries["http://www.example.com/entry/1"]
        
        self.assertEqual(entry1["hash"], "01234")
        self.assertEqual(entry1["type"], "data")
        self.assertEqual(entry1["description"], "example description 1")

    def test_StatusList_as_xml(self):
        msg = message.StatusList()
        msg.add(id="task-1", state="Pending", meta={"submit-time": 1171983221,
                                                    "start-time": 1171983221,
                                                    "end-time": 1171983221,
                                                    "foo": {1: "a"},
                                                    })
        xml = msg.as_xml()
        elem = xml.find(XBE("MessageBody")+"/"+msg.tag)
        self.assertNotEqual(elem, None)
        status = elem.getchildren()[0]
        self.assertEqual(status.attrib["task-id"], "task-1")

    def test_StatusList_from_xml(self):
        xml = """
        <xbe:Message xmlns:xbe="http://www.example.com/schemas/xbe/2007/01/xbe">
           <xbe:MessageHeader/>
           <xbe:MessageBody>
             <xbe:StatusList>
               <xbe:Status task-id="task-1">
                 <bes:ActivityStatus xmlns:bes="http://schemas.ggf.org/bes/2006/08/bes-activity"
                                       state="Pending"/>
                 <xbe:Meta>
                   <xbe:Dict>
                      <xbe:Entry key="submit-time">1171983221</xbe:Entry>
                   </xbe:Dict>   
                 </xbe:Meta>
               </xbe:Status>
             </xbe:StatusList>
           </xbe:MessageBody>
        </xbe:Message>
        """
        msg = message.MessageBuilder.from_xml(etree.fromstring(xml))
        self.assertTrue(isinstance(msg, message.StatusList))
        self.assertTrue("task-1" in msg.entries().keys())
        entry = msg.entries()["task-1"]
        self.assertEqual(entry["Meta"]["submit-time"], "1171983221")
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
        self.assertEqual(elem.attrib["inst-id"], "test-instance-id")

        ip = elem.findtext(XBE("NodeInformation/Network/IPList/IP"))
        self.assertEqual(ip, "127.0.0.1")

    def test_InstanceAvailable_from_xml(self):
        xml = """
        <xbe:Message xmlns:xbe="http://www.example.com/schemas/xbe/2007/01/xbe">
          <xbe:MessageHeader/>
          <xbe:MessageBody>
            <xbe:InstanceAvailable inst-id="test-instance-id">
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
        
    def test_InstanceAlive_as_xml(self):
        msg = message.InstanceAlive(inst_id="instance 1", uptime=1171983221)
        xml = msg.as_xml()
        elem = xml.find(XBE("MessageBody")+"/"+msg.tag)
        self.assertNotEqual(elem, None)
        self.assertEqual(elem.attrib.get("inst-id"), "instance 1")
        self.assertEqual(int(elem.findtext(XBE("Uptime"))), 1171983221)

    def test_InstanceAlive_from_xml(self):
        xml = """
        <xbe:Message xmlns:xbe="http://www.example.com/schemas/xbe/2007/01/xbe">
          <xbe:MessageHeader/>
          <xbe:MessageBody>
            <xbe:InstanceAlive inst-id="instance 1">
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

    def test_StatusRequest_as_xml(self):
        msg = message.StatusRequest("ticket 1")
        xml = msg.as_xml()
        elem = xml.find(XBE("MessageBody")+"/"+msg.tag)
        self.assertNotEqual(elem, None)
        res = elem.find(XBE("Reservation/Ticket"))
        self.assertNotEqual(res, None)
        self.assertEqual(res.text, "ticket 1")

    def test_StatusRequest_from_xml(self):
        xml = """<xbe:Message xmlns:xbe="http://www.example.com/schemas/xbe/2007/01/xbe"><xbe:MessageHeader/><xbe:MessageBody><xbe:StatusRequest><xbe:Reservation><xbe:Ticket>ticket-1</xbe:Ticket></xbe:Reservation></xbe:StatusRequest></xbe:MessageBody></xbe:Message>"""
        msg = message.MessageBuilder.from_xml(xml)
        self.assertTrue(isinstance(msg, message.StatusRequest))
        self.assertEqual(msg.ticket(), "ticket-1")

def suite():
    s1 = unittest.makeSuite(TestServerMessages, 'test')
    s2 = unittest.makeSuite(TestInstanceMessages, 'test')
    s3 = unittest.makeSuite(TestClientMessages, 'test')
    return unittest.TestSuite((s1,s2,s3))

if __name__ == '__main__':
    unittest.main()

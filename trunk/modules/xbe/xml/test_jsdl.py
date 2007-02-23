#!/usr/bin/python

"""Test for the jsdl module."""

__version__ = "$Rev$"
__author__ = "$Author$"

import unittest, os, sys
from xbe.xml import jsdl
from lxml import etree
from xbe.xml.namespaces import *

class TestRangeValue(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_lower_bound_range_exclusive(self):
        rv = jsdl.RangeValue( lower=(0.0, True) )
        self.assertTrue(rv.matches(0.1))
        self.assertTrue(rv.matches(100))
        self.assertFalse(rv.matches(0.0))
        self.assertFalse(rv.matches(-1))

    def test_lower_bound_range(self):
        rv = jsdl.RangeValue(lower=(10.0, False))
        self.assertTrue(rv.matches(10.0))
        self.assertTrue(rv.matches(100))
        self.assertFalse(rv.matches(9.9))
        self.assertFalse(rv.matches(0))

    def test_upper_bound_range_exclusive(self):
        rv = jsdl.RangeValue( upper=(0.0, True) )
        self.assertTrue(rv.matches(-0.1))
        self.assertTrue(rv.matches(-10))
        self.assertFalse(rv.matches(0.0))
        self.assertFalse(rv.matches(200))

    def test_upper_bound_range(self):
        rv = jsdl.RangeValue(upper=(10.0, False))
        self.assertTrue(rv.matches(10.0))
        self.assertTrue(rv.matches(9))
        self.assertFalse(rv.matches(11))
        self.assertFalse(rv.matches(200))

    def test_lower_upper_bound_range(self):
        rv = jsdl.RangeValue( lower=(0.0, True), upper=(10.0, False) )
        self.assertTrue(rv.matches(1))
        self.assertTrue(rv.matches(200))
        self.assertTrue(rv.matches(-1))
        self.assertTrue(rv.matches(0.0))

    def test_exacts(self):
        rv = jsdl.RangeValue(exacts=( (5, 0.0), (10, 2) ))
        self.assertTrue(rv.matches(10.0))
        self.assertTrue(rv.matches(8))
        self.assertTrue(rv.matches(12))
        self.assertFalse(rv.matches(5.1))
        self.assertFalse(rv.matches(4.9))
        self.assertFalse(rv.matches(7.9))
                        
    def test_ranges(self):
        rv = jsdl.RangeValue(ranges=( ((5, True), (10, False)),
                                      ((0, False), (3, True))))
        self.assertTrue(rv.matches(6))
        self.assertTrue(rv.matches(8))
        self.assertFalse(rv.matches(12))
        self.assertFalse(rv.matches(4))
        self.assertTrue(rv.matches(2.3))
        self.assertTrue(rv.matches(0))

    def test_jsdl_example(self):
        rv = jsdl.RangeValue(lower=(100.0, False),
                             exacts=((5.0, 0), (6.7777, 0.00001), (7.0, 0)),
                             ranges=( ((50.3, False), (99.5, True)), ))
        self.assertTrue(rv.matches(5))
        self.assertTrue(rv.matches(6.7777))
        self.assertTrue(rv.matches(55))
        self.assertTrue(rv.matches(98))

        self.assertFalse(rv.matches(99.5))
        self.assertFalse(rv.matches(99.9))

        self.assertTrue(rv.matches(100))

    def test_as_xml(self):
        rv = jsdl.RangeValue(lower=(100.0, False),
                             exacts=((5.0, 0), (6.7777, 0.00001), (7.0, 0)),
                             ranges=( ((50.3, False), (99.5, True)), ))
        tmp = etree.Element("TestRange")
        rv.as_xml(tmp)
        self.assertEqual(tmp.findtext(JSDL("LowerBoundedRange")), str(100.0))

    def test_from_xml(self):
        xml = """
        <TestRange>
           <ns0:LowerBoundedRange xmlns:ns0="http://schemas.ggf.org/jsdl/2005/11/jsdl"
                                  exclusiveBound="False">
               100.0
           </ns0:LowerBoundedRange>
           <ns0:Exact xmlns:ns0="http://schemas.ggf.org/jsdl/2005/11/jsdl"
                      epsilon="0">
               5.0
           </ns0:Exact>
           <ns0:Exact xmlns:ns0="http://schemas.ggf.org/jsdl/2005/11/jsdl"
                      epsilon="1e-05">
               6.7777
           </ns0:Exact>
           <ns0:Exact xmlns:ns0="http://schemas.ggf.org/jsdl/2005/11/jsdl"
                      epsilon="0">
               7.0
           </ns0:Exact>
           <ns0:Range xmlns:ns0="http://schemas.ggf.org/jsdl/2005/11/jsdl">
               <ns0:LowerBound exclusiveBound="False">50.3</ns0:LowerBound>
               <ns0:UpperBound exclusiveBound="True">99.5</ns0:UpperBound>
            </ns0:Range>
        </TestRange>
        """
        rv = jsdl.RangeValue.from_xml(etree.fromstring(xml))
        self.assertTrue(rv.matches(5))
        self.assertTrue(rv.matches(6.7777))
        self.assertTrue(rv.matches(55))
        self.assertTrue(rv.matches(98))

        self.assertFalse(rv.matches(99.5))
        self.assertFalse(rv.matches(99.9))

        self.assertTrue(rv.matches(100))


class TestJsdlParser(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_simple(self):
        xml = """
        <ns0:JobDefinition xmlns:ns0="http://schemas.ggf.org/jsdl/2005/11/jsdl"
                           xmlns:jsdl-posix="http://schemas.ggf.org/jsdl/2005/11/jsdl-posix">
          <ns0:JobDescription>
             <ns0:JobIdentification>
               <ns0:JobName>foobar</ns0:JobName>
               <ns0:Description>blah</ns0:Description>
               <ns0:JobAnnotation>anno 1</ns0:JobAnnotation>
               <ns0:JobAnnotation>anno 2</ns0:JobAnnotation>
               <ns0:JobAnnotation>anno 3</ns0:JobAnnotation>
             </ns0:JobIdentification>
             <ns0:Application>
               <ns0:ApplicationName>test app name</ns0:ApplicationName>
               <ns0:ApplicationVersion>4.3</ns0:ApplicationVersion>
               <jsdl-posix:POSIXApplication>
                 <jsdl-posix:Executable>
                    /usr/local/bin/gnuplot
                 </jsdl-posix:Executable>
                 <jsdl-posix:Argument>control.txt</jsdl-posix:Argument>
                 <jsdl-posix:Argument>control.txt</jsdl-posix:Argument>
                 <jsdl-posix:Argument>control.txt</jsdl-posix:Argument>
                 <jsdl-posix:Input>input.dat</jsdl-posix:Input>
                 <jsdl-posix:Output>output1.png</jsdl-posix:Output>
               </jsdl-posix:POSIXApplication>
             </ns0:Application>
             <ns0:Resources>
               <ns0:ExclusiveExecution>true</ns0:ExclusiveExecution>
               <ns0:FileSystem name="ROOT">
                  <ns0:Description>home filesystem</ns0:Description>
                  <ns0:MountPoint>/</ns0:MountPoint>
                  <ns0:MountSource>file:///srv/xen-images/xenbee/base.img</ns0:MountSource>
                  <Extension>test</Extension>
               </ns0:FileSystem>
               <ns0:FileSystem name="HOME">
                  <ns0:Description>home filesystem</ns0:Description>
                  <ns0:MountPoint>/</ns0:MountPoint>
                  <ns0:MountSource>file:///srv/xen-images/xenbee/base.img</ns0:MountSource>
                  <ns0:DiskSpace>
                     <ns0:LowerBoundedRange>1073741824</ns0:LowerBoundedRange>
                  </ns0:DiskSpace>
                  <ns0:FileSystemType>normal</ns0:FileSystemType>
               </ns0:FileSystem>
               <ns0:CandidateHosts>
                 <ns0:HostName>host1</ns0:HostName>
                 <ns0:HostName>host2</ns0:HostName>                 
                 <ns0:HostName>host3</ns0:HostName>                 
               </ns0:CandidateHosts>
               <ns0:OperatingSystem>
                 <ns0:OperatingSystemType>
                    <ns0:OperatingSystemName>Linux</ns0:OperatingSystemName>
                 </ns0:OperatingSystemType>
                 <ns0:OperatingSystemVersion>2.6.11</ns0:OperatingSystemVersion>
               </ns0:OperatingSystem>
               <ns0:CPUArchitecture>
                  <ns0:CPUArchitectureName>x86</ns0:CPUArchitectureName>
               </ns0:CPUArchitecture>
             </ns0:Resources>
             <ns0:DataStaging>
                <ns0:FileName>test.file</ns0:FileName>
                <ns0:FileSystemName>HOME</ns0:FileSystemName>
                <ns0:Source>
                   <ns0:URI>http://www.example.com/test.file</ns0:URI>
                </ns0:Source>
                <ns0:Target>
                   <ns0:URI>http://www.example.com/test.file</ns0:URI>
                </ns0:Target>
                <ns0:CreationFlag>overwrite</ns0:CreationFlag>
                <ns0:DeleteOnTermination>true</ns0:DeleteOnTermination>
             </ns0:DataStaging>
          </ns0:JobDescription>
        </ns0:JobDefinition>
        """
        elem = etree.fromstring(xml)
        doc = jsdl.JsdlDocument()
        from pprint import pprint
        pprint(doc._parse(elem))
        
def suite():
    s1 = unittest.makeSuite(TestRangeValue, 'test')
    return unittest.TestSuite((s1,))

if __name__ == '__main__':
    unittest.main()

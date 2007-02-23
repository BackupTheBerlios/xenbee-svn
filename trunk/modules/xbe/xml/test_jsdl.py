#!/usr/bin/python

"""Test for the jsdl module."""

__version__ = "$Rev$"
__author__ = "$Author$"

import unittest, os, sys
from pprint import pprint

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
        <jsdl:JobDefinition xmlns:jsdl="http://schemas.ggf.org/jsdl/2005/11/jsdl"
                           xmlns:jsdl-posix="http://schemas.ggf.org/jsdl/2005/11/jsdl-posix">
          <jsdl:JobDescription>
             <jsdl:JobIdentification>
               <jsdl:JobName>foobar</jsdl:JobName>
               <jsdl:Description>blah</jsdl:Description>
               <jsdl:JobAnnotation>anno 1</jsdl:JobAnnotation>
               <jsdl:JobAnnotation>anno 2</jsdl:JobAnnotation>
               <jsdl:JobAnnotation>anno 3</jsdl:JobAnnotation>
             </jsdl:JobIdentification>
             <jsdl:Application>
               <jsdl:ApplicationName>test app name</jsdl:ApplicationName>
               <jsdl:ApplicationVersion>4.3</jsdl:ApplicationVersion>
               <jsdl-posix:POSIXApplication>
                 <jsdl-posix:Executable>
                    /usr/local/bin/gnuplot
                 </jsdl-posix:Executable>
                 <jsdl-posix:Argument>arg1</jsdl-posix:Argument>
                 <jsdl-posix:Argument>arg2</jsdl-posix:Argument>
                 <jsdl-posix:Argument><!-- empty arg--></jsdl-posix:Argument>
                 <jsdl-posix:Argument>arg4</jsdl-posix:Argument>
                 <jsdl-posix:Input>input.dat</jsdl-posix:Input>
                 <jsdl-posix:Output>output1.png</jsdl-posix:Output>
               </jsdl-posix:POSIXApplication>
             </jsdl:Application>
             <jsdl:Resources>
               <jsdl:ExclusiveExecution>true</jsdl:ExclusiveExecution>
               <jsdl:FileSystem name="ROOT">
                  <jsdl:Description>the root filesystem</jsdl:Description>
                  <jsdl:MountPoint>/</jsdl:MountPoint>
                  <jsdl:DiskSpace>
                     <jsdl:Exact epsilon="5.0">1073741824</jsdl:Exact>
                  </jsdl:DiskSpace>
                  <xsdl:Image xmlns:xsdl="http://www.example.com/schemas/xbe/2007/01/xsdl">
                     <jsdl:URI>file:///srv/xen-images/xenbee/usr.img</jsdl:URI>
                  </xsdl:Image>
               </jsdl:FileSystem>
               <jsdl:FileSystem name="USR_LOCAL">
                  <jsdl:Description>the user local</jsdl:Description>
                  <jsdl:MountPoint>/usr/local</jsdl:MountPoint>
                  <jsdl:MountSource>file:///srv/xen-images/xenbee/usr.img</jsdl:MountSource>
                  <jsdl:DiskSpace>
                     <jsdl:LowerBoundedRange>1073741824</jsdl:LowerBoundedRange>
                  </jsdl:DiskSpace>
                  <jsdl:FileSystemType>normal</jsdl:FileSystemType>
               </jsdl:FileSystem>
               <jsdl:FileSystem name="SPOOL">
                  <jsdl:Description>a spool filesystem</jsdl:Description>
                  <jsdl:MountPoint>/spool</jsdl:MountPoint>
                  <jsdl:DiskSpace>
                     <jsdl:LowerBoundedRange>1073741824</jsdl:LowerBoundedRange>
                  </jsdl:DiskSpace>
                  <jsdl:FileSystemType>temporary</jsdl:FileSystemType>
               </jsdl:FileSystem>
               <jsdl:CandidateHosts>
                 <jsdl:HostName>host1</jsdl:HostName>
                 <jsdl:HostName>host2</jsdl:HostName>                 
                 <jsdl:HostName>host3</jsdl:HostName>                 
               </jsdl:CandidateHosts>
               <jsdl:OperatingSystem>
                 <jsdl:OperatingSystemType>
                    <jsdl:OperatingSystemName>Linux</jsdl:OperatingSystemName>
                 </jsdl:OperatingSystemType>
                 <jsdl:OperatingSystemVersion>2.6.11</jsdl:OperatingSystemVersion>
               </jsdl:OperatingSystem>
               <jsdl:CPUArchitecture>
                  <jsdl:CPUArchitectureName>x86</jsdl:CPUArchitectureName>
               </jsdl:CPUArchitecture>
               <jsdl:TotalCPUCount>
                  <jsdl:Exact>2</jsdl:Exact>
               </jsdl:TotalCPUCount>
               <xbe:Reservation xmlns:xbe="http://www.example.com/schemas/xbe/2007/01/xbe">
                  <xbe:Ticket>ticket-1</xbe:Ticket>
               </xbe:Reservation>
               <xsdl:Instance xmlns:xsdl="http://www.example.com/schemas/xbe/2007/01/xsdl">
                  <xsdl:PackageDefinition>
                     <xsdl:PackageLocation compressed="bzip2">
                        <jsdl:URI>file:///srv/xen-images/package.tar.bz2</jsdl:URI>
                     </xsdl:PackageLocation>
                  </xsdl:PackageDefinition>
                  <xsdl:KernelDefinition>
                     <xsdl:Argument></xsdl:Argument>
                     <xsdl:Kernel>
                        <jsdl:URI>file:///srv/xen-images/domains/xenhobel-2/kernel</jsdl:URI>
                     </xsdl:Kernel>
                     <xsdl:Initrd>
                        <jsdl:URI>file:///srv/xen-images/domains/xenhobel-2/initrd</jsdl:URI>
                        <xbe:CacheID xmlns:xbe="http://www.example.com/schemas/xbe/2007/01/xbe">
                           abcd
                        </xbe:CacheID>
                     </xsdl:Initrd>
                  </xsdl:KernelDefinition>
               </xsdl:Instance>
             </jsdl:Resources>
             <jsdl:DataStaging>
                <jsdl:FileName>test.file</jsdl:FileName>
                <jsdl:FileSystemName>HOME</jsdl:FileSystemName>
                <jsdl:Source>
                   <jsdl:URI>http://www.example.com/test.file</jsdl:URI>
                </jsdl:Source>
                <jsdl:Target>
                   <jsdl:URI>http://www.example.com/test.file</jsdl:URI>
                </jsdl:Target>
                <jsdl:CreationFlag>overwrite</jsdl:CreationFlag>
                <jsdl:DeleteOnTermination>true</jsdl:DeleteOnTermination>
             </jsdl:DataStaging>
          </jsdl:JobDescription>
        </jsdl:JobDefinition>
        """
        elem = etree.fromstring(xml)
        doc = jsdl.JsdlDocument()
        pprint(doc._parse(elem))
        
def suite():
    s1 = unittest.makeSuite(TestRangeValue, 'test')
    return unittest.TestSuite((s1,))

if __name__ == '__main__':
    unittest.main()

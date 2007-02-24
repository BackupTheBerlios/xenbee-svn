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


class TestHashValidator(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_valid(self):
        validator = jsdl.HashValidator('430ce34d020724ed75a196dfc2ad67c77772d169', "sha1")
        self.assertTrue(validator.validate('hello world!'))

    def test_invalid(self):
        validator = jsdl.HashValidator('0123456789abcdef', "sha1")
        self.assertFalse(validator.validate('hello world!'))

class TestJsdlParser(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_simple(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>

<!-- image submission extension for JSDL -->

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
      <jsdl:FileSystem name="ROOT">
	<jsdl:Description>the root filesystem</jsdl:Description>
	<jsdl:MountPoint>/</jsdl:MountPoint>
      </jsdl:FileSystem>
      <jsdl:FileSystem name="SPOOL">
	<jsdl:Description>a spool directory</jsdl:Description>
	<jsdl:MountPoint>/spool</jsdl:MountPoint>
      </jsdl:FileSystem>
      <jsdl:TotalCPUCount>
	<jsdl:Exact>2</jsdl:Exact>
      </jsdl:TotalCPUCount>


      <!-- XBE reservation extension -->
      <xbe:Reservation xmlns:xbe="http://www.example.com/schemas/xbe/2007/01/xbe">
	<xbe:Ticket>ticket-1</xbe:Ticket>
      </xbe:Reservation>
      
      <xsdl:InstanceDefinition xmlns:xsdl="http://www.example.com/schemas/xbe/2007/01/xsdl">
	<!-- user may specify either a package or the the instance itself -->
	<xsdl:Package>
          <xsdl:Description>
             A sample description for this package
          </xsdl:Description>
	  <xsdl:Location compressed="tbz">
	    <xsdl:URI>file:///srv/xen-images/package.tar.bz2</xsdl:URI>
	    <xsdl:Hash algorithm="sha1">0123456789</xsdl:Hash>
	  </xsdl:Location>
	</xsdl:Package>

	<xsdl:InstanceDescription>
	  <!-- the kernel must be specified if using the InstanceDescription -->
	  <xsdl:Kernel>
	    <xsdl:Argument name="foo">bar</xsdl:Argument> <!-- results in 'foo=bar' -->
	    <xsdl:Argument>bar</xsdl:Argument> <!-- results in 'bar' -->
	    <xsdl:Location>
	      <xsdl:Hash algorithm="sha1">0123456789</xsdl:Hash>
	      <xbe:CacheEntry xmlns:xbe="http://www.example.com/schemas/xbe/2007/01/xbe">
		uuid:0123456789
	      </xbe:CacheEntry>
	    </xsdl:Location>
	  </xsdl:Kernel>

	  <!-- the initrd is optional -->
	  <xsdl:Initrd>
	    <xsdl:Location>
	      <xsdl:URI>file:///srv/xen-images/domains/xenhobel-2/initrd</xsdl:URI>
	      <xsdl:Hash algorithm="sha1">0123456789</xsdl:Hash>
	    </xsdl:Location>
	  </xsdl:Initrd>
	</xsdl:InstanceDescription>
      </xsdl:InstanceDefinition>

    </jsdl:Resources>
    <jsdl:DataStaging>
      <jsdl:FileName>test.file</jsdl:FileName>
      <jsdl:FilesystemName>HOME</jsdl:FilesystemName>
      <jsdl:CreationFlag>overwrite</jsdl:CreationFlag>
      <jsdl:DeleteOnTermination>true</jsdl:DeleteOnTermination>
      <jsdl:Source>
	<jsdl:URI>http://www.example.com/test.file</jsdl:URI>
      </jsdl:Source>
      <jsdl:Target>
	<jsdl:URI>http://www.example.com/test.file</jsdl:URI>
      </jsdl:Target>
    </jsdl:DataStaging>
  </jsdl:JobDescription>
</jsdl:JobDefinition>
        """
        elem = etree.fromstring(xml)
        schema_path = "/root/xenbee/etc/xml/schema/jsdl.xsd"
        jsdl_schema = etree.XMLSchema(etree.parse(schema_path))
        doc = jsdl.JsdlDocument()
        doc.register_schema(str(JSDL), jsdl_schema)
        pprint(doc.parse(elem))
        
def suite():
    s1 = unittest.makeSuite(TestRangeValue, 'test')
    return unittest.TestSuite((s1,))

if __name__ == '__main__':
    unittest.main()

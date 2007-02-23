#!/usr/bin/env python
"""
A module, that provides a JSDL parser and generator.
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging
log = logging.getLogger(__name__)

from lxml import etree
from xbe.xml.namespaces import *
from xbe.xml import errcode

JSDL_ProcessorArchitectureEnumeration = [ "x86", "x86_32" ]
JSDL_FileSystemTypeEnumeration = [ "swap", "temporary", "spool", "normal" ]
JSDL_OperatingSystemTypeEnumeration = [ "Linux" ]
JSDL_CreationFlagEnumeration = [ "overwrite", "dontOverwrite", "append" ]

class RangeValue:
    def __init__(self,
                 lower=(None, False), upper=(None, False),
                 exacts=[], ranges=[]):
        self.lower = lower
        self.upper = upper
        self.exacts = [e for e in exacts]  # list of (exact, epsilon) tuples
        self.ranges = [r for r in ranges]  # list of (lower, upper) tuples of tuples

    def __matches_lower(self, value, bound, exclusive):
        if exclusive:
            return value > bound
        else:
            return value >= bound
    def __matches_upper(self, value, bound, exclusive):
        if exclusive:
            return value < bound
        else:
            return value <= bound
    def __matches_range(self, value, lower, upper):
        return self.__matches_lower(value, *lower) and \
               self.__matches_upper(value, *upper)
    def __matches_exact(self, value, exact, epsilon):
        return ((exact-epsilon) <= value) and (value <= (exact+epsilon))

    def add_range(self, lower, upper):
        self.ranges.append( (lower, upper) )
    def add_exact(self, exact, epsilon):
        self.exacts.append( (exact, epsilon) )
    def set_lower(self, lower):
        self.lower = lower
    def set_upper(self, upper):
        self.upper = upper

    def matches(self, value):
        if self.upper[0] is not None:
            if self.__matches_upper(value, *self.upper):
                return True
        if self.lower[0] is not None:
            if self.__matches_lower(value, *self.lower):
                return True
        for exact in self.exacts:
            if self.__matches_exact(value, *exact):
                return True
        for range in self.ranges:
            if self.__matches_range(value, *range):
                return True
        return False

    def __parse_range_type(self, xml_elem):
        ns, tag = decodeTag(xml_elem.tag)
        if ns != str(JSDL):
            raise ValueError("unknown namespace found", ns, tag)
        parser = getattr(self, "_from_xml_%s" % tag)
        parser(xml_elem)

    def _from_xml_LowerBoundedRange(self, xml_elem):
        self.set_lower(self._parse_BoundedRange(xml_elem))
    def _from_xml_UpperBoundedRange(self, xml_elem):
        self.set_upper(self._parse_BoundedRange(xml_elem))
    def _from_xml_Exact(self, xml_elem):
        self.add_exact(*self._parse_Exact(xml_elem))
    def _from_xml_Range(self, xml_elem):
        self.add_range(*self._parse_Range(xml_elem))

    def _parse_BoundedRange(self, xml_elem):
        exclusive = xml_elem.attrib.get("exclusiveBound", "False")
        if exclusive == "False":
            exclusive = False
        else:
            exclusive = True
        return (float(xml_elem.text), exclusive)
    def _parse_Range(self, xml_elem):
        return (self._parse_BoundedRange(xml_elem.find(JSDL("LowerBound"))),
                self._parse_BoundedRange(xml_elem.find(JSDL("UpperBound"))))
    def _parse_Exact(self, xml_elem):
        return (float(xml_elem.text), float(xml_elem.attrib.get("epsilon", 0.0)))

    def as_xml(self, parent=None):
        """returns the XML representation of this RangeValue.

        if parent is None (default), a list of xml elements is
        returned, else, they are appended to the parent
        """
        elems = []
        if self.lower[0]:
            e = etree.Element(JSDL("LowerBoundedRange"))
            e.text = str(self.lower[0])
            e.attrib["exclusiveBound"] = str(self.lower[1])
            elems.append(e)
        if self.upper[0]:
            e = etree.Element(JSDL("UpperBoundedRange"))
            e.text = str(self.upper[0])
            e.attrib["exclusiveBound"] = str(self.lower[1])
            elems.append(e)
        for exact, epsilon in self.exacts:
            e = etree.Element(JSDL("Exact"))
            e.text = str(exact)
            e.attrib["epsilon"] = str(epsilon)
            elems.append(e)
        for lower, upper in self.ranges:
            e = etree.Element(JSDL("Range"))
            e_lo = etree.SubElement(e, JSDL("LowerBound"))
            e_lo.text = str(lower[0])
            e_lo.attrib["exclusiveBound"] = str(lower[1])
            e_hi = etree.SubElement(e, JSDL("UpperBound"))
            e_hi.text = str(upper[0])
            e_hi.attrib["exclusiveBound"] = str(upper[1])
            elems.append(e)
        if parent is not None:
            for e in elems:
                parent.append(e)
            return parent
        return elems

    def from_xml(cls, elem):
        # elem contains the range specifications as its child elements
        rv = cls()
        for range_type in elem:
            rv.__parse_range_type(range_type)
        return rv
    from_xml = classmethod(from_xml)

class JsdlDocument:
    DEFAULT_PARSER=()
    
    def __init__(self):

        # JSDL Parser Map
        jsdlParserMap = {
            self.DEFAULT_PARSER: self._parse_complex,
            "JobDefinition": self._parse_start,
            
            # JobIdentification
            "Description": self._parse_text,
            "JobName": self._parse_text,
            "JobAnnotation": self._parse_text_array,
            "JobProject": self._parse_text_array,

            # Application
            "ApplicationName": self._parse_text,
            "ApplicationVersion": self._parse_text,

            # Resources
            "CandidateHosts": self._parse_elem_array,
            "HostName": self._parse_text,
            "FileSystem": self._parse_complex_array,
            "MountPoint": self._parse_text,
            "MountSource": self._parse_text,
            "DiskSpace": self._parse_range,
            "FileSystemType": self._parse_text,
            "ExclusiveExecution": self._parse_bool,
            "OperatingSystemName": self._parse_text,
            "OperatingSystemVersion": self._parse_text,
            "CPUArchitectureName": self._parse_text,

            "IndividualCPUSpeed": self._parse_range,
            "IndividualCPUTime": self._parse_range,
            "IndividualCPUCount": self._parse_range,
            "IndividualNetworkBandwidth": self._parse_range,
            "IndividualPhysicalMemory": self._parse_range,
            "IndividualVirtualMemory": self._parse_range,
            "IndividualDiskSpace": self._parse_range,
            "TotalCPUTime": self._parse_range,
            "TotalCPUCount": self._parse_range,
            "TotalPhysicalMemory": self._parse_range,
            "TotalVirtualMemory": self._parse_range,
            "TotalDiskSpace": self._parse_range,
            "TotalResourceCount": self._parse_range,

            # DataStaging
            "DataStaging": self._parse_complex_array,
            "FileName": self._parse_text,
            "FileSystemName": self._parse_text,
            "URI": self._parse_uri,
            "CreationFlag": self._parse_text,
            "DeleteOnTermination": self._parse_bool,
            }

        # JSDL-POSIX Parser Map
        jsdlPosixParserMap = {
            self.DEFAULT_PARSER: self._parse_complex,
            "Executable": self._parse_text,

            # TODO: this must be changed, since the 'Argument' accepts an attribute!!!!
            "Argument": self._parse_posix_text_array,
            "Executable": self._parse_posix_text,
            "Input": self._parse_posix_text,
            "Output": self._parse_posix_text,
            "Error": self._parse_posix_text,
            "WorkingDirectory": self._parse_posix_text,
            "Environment": self._parse_posix_text_array,
            "WallTimeLimit": self._parse_unsigned_integer,
            "FileSizeLimit": self._parse_unsigned_integer,
            "DataSegmentLimit": self._parse_unsigned_integer,
            "LockedMemoryLimit": self._parse_unsigned_integer,
            "MemoryLimit": self._parse_unsigned_integer,
            "OpenDescriptorsLimit": self._parse_unsigned_integer,
            "PipeSizeLimit": self._parse_unsigned_integer,
            "StackSizeLimit": self._parse_unsigned_integer,
            "CPUTimeLimit": self._parse_unsigned_integer,
            "ProcessCountLimit": self._parse_unsigned_integer,
            "VirtualMemoryLimit": self._parse_unsigned_integer,
            "ThreadCountLimit": self._parse_unsigned_integer,
            "UserName": self._parse_text,
            "GroupName": self._parse_text,
            }

        self.parserMaps = {
            str(JSDL): jsdlParserMap,
            str(JSDL_POSIX): jsdlPosixParserMap,
            }

    def lookup_path(self, path):
        components = path.split("/")
        elem = self.__parsed_doc
        for c in components:
            elem = elem[c]
        return elem

    def _parse_complex(self, xml):
        children = {}
        if len(xml.attrib):
            children[":attributes:"] = {}
            for k,v in xml.attrib.iteritems():
                children[":attributes:"][k] = v
        for e in xml:
            if isinstance(e, etree._Comment):
                continue
            ns, child_tag = decodeTag(e.tag)
            if ns not in self.parserMaps.keys():
                other = children.get("other")
                if other is None:
                    other = []
                    children["other"] = other
                other.append(self._parse(e))
            else:
                mapping = children.get(child_tag)
                if mapping is not None and isinstance(mapping, list):
                    mapping.extend(self._parse(e))
                else:
                    children[child_tag] = self._parse(e)
        return children

    def _parse(self, xml_elem):
        ns, tag = decodeTag(xml_elem.tag)
        # get the parser map
        parser_map = self.parserMaps.get(ns)
        if parser_map is None:
            # cannot find a suitable parsermap
            return xml_elem
        parser = parser_map.get(tag, parser_map[self.DEFAULT_PARSER])
        return parser(xml_elem)

    def _parse_start(self, xml):
        tag = decodeTag(xml.tag)[1]
        self.__parsed_doc = {}
        self.__parsed_doc[tag] = { decodeTag(xml[0].tag)[1]: self._parse(xml[0]) }
        return self.__parsed_doc

    def _parse_elem_array(self, xml):
        return [self._parse(xml[0])]
    def _parse_text_array(self, xml):
        return [xml.text]
    def _parse_text(self, xml):
        return xml.text
    def _parse_uri(self, xml):
        return self._parse_text(xml)
    def _parse_complex_array(self, xml):
        return [self._parse_complex(xml)]
    def _parse_range(self, xml):
        return RangeValue.from_xml(xml)
    def _parse_bool(self, xml):
        val = (xml.text or "").strip().lower()
        if val in ("true", "yes", "1"):
            return True
        elif val in ("false", "no", "0"):
            return False
        else:
            raise ValueError("illegal value for bool", val)

    def _parse_integer(self, xml):
        return int(xml.text)
    def _parse_unsigned_integer(self, xml):
        i = self._parse_integer(xml)
        if i < 0:
            raise ValueError("nonNegativeInteger expected", i)
        return i

    def _parse_posix_text_array(self, xml):
        # return a tuple (filesystemName attribute, xml.text)
        return [self._parse_posix_text(xml)]
    def _parse_posix_text(self, xml):
        return ((xml.text or "").strip(), dict(xml.attrib))

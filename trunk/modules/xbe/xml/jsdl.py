#!/usr/bin/env python
"""A module, that provides a JSDL parser.

This is a *premature hack*. One should refactor it into a generic
parser frame-work to which an application can attach more
functionality. But I did not have time to that refactoring yet.
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging, hashlib, sys
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

    def __str__(self):
        s = []
        if self.upper[0] is not None:
            if self.upper[1]:
                s.append("< %.2f" % self.upper[0])
            else:
                s.append("<= %.2f" % self.upper[0])
        if self.lower[0] is not None:
            if self.lower[1]:
                s.append("> %.2f" % self.lower[0])
            else:
                s.append(">= %.2f" % self.lower[0])
        for exact, epsilon in self.exacts:
            if epsilon != 0:
                s.append("== %.2f (+/- %f)" % (exact, epsilon))
            else:
                s.append("== %.2f" % (exact))
        for lower, upper in self.ranges:
            s.append("%(lo_bound)s%(lo_val)f, %(hi_val)s%(hi_bound)s" % {
                "lo_bound": lower[1] and "(" or "[",
                "lo_val": lower[0],
                "hi_val": upper[0],
                "hi_bound": upper[1] and ")" or "]"
            })
        return "{"+", ".join(s)+"}"

    def __repr__(self):
        return "<%(cls)s %(humanreadable)s>" % {
            "cls": self.__class__.__name__,
            "humanreadable": str(self)
            }

    def get_value(self):
        if len(self.exacts) == 1:
            return self.exacts[0][0]
        raise NotImplementedError("TODO: implement more functionality")

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

class HashValidator:
    """Represents a hash algorithm validator.

    Its only defined method is 'validate' which accepts some data and
    returns True if and only if the stored digest matches the one
    computed out of the data using the stored hash-algorithm.
    """
    
    def __init__(self, hexdigest, algorithm="sha1"):
        """Initialize the HashValidator.

        The parameters to this can be retrieved from an xml document.
        """
        self.__hexdigest = hexdigest
        self.__algorithm = algorithm

    def validate(self, data):
        """Validate the data against the stored digest using the
        stored algorithm."""
        h = hashlib.new(self.__algorithm)
        h.update(data)
        return self.__hexdigest == h.hexdigest()

    def __call__(self, data):
        """Does the same as 'validate(data)'."""
        return self.validate(data)

    def __repr__(self):
        return "<%(cls)s using %(algo)s with digest %(digest)s>" % {
            "cls": self.__class__.__name__,
            "digest": self.__hexdigest,
            "algo": self.__algorithm
        }

class JsdlDocument:
    DEFAULT_PARSER=()
    
    def __init__(self):
        self._schemaMap = {}
        self._fileSystems = {}

        # JSDL Parser Map
        jsdlParserMap = {
            self.DEFAULT_PARSER: self._parse_complex,
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
            "FileSystem": self._parse_filesystem,
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
            "FilesystemName": self._parse_text,
            "URI": self._parse_uri,
            "CreationFlag": self._parse_text,
            "DeleteOnTermination": self._parse_bool,
            }

        # JSDL-POSIX Parser Map
        jsdlPosixParserMap = {
            self.DEFAULT_PARSER: self._parse_complex,
            "Executable": self._parse_text,

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

        xbeParserMap = {
            self.DEFAULT_PARSER: self._parse_complex,
            "Ticket": self._parse_normative_text,
            "CacheID": self._parse_normative_text,
        }
        xsdlParserMap = {
            self.DEFAULT_PARSER: self._parse_complex,
            "Argument": self._parse_xsdl_argument,
            "URI": self._parse_normative_text,
            "CacheEntry": self._parse_normative_text,
            "Hash": self._parse_hash,
        }

        self.parserMaps = {
            str(JSDL): jsdlParserMap,
            str(JSDL_POSIX): jsdlPosixParserMap,
            str(XBE): xbeParserMap,
            str(XSDL): xsdlParserMap,
        }

    def register_schema(self, namespace, schema):
        self._schemaMap[namespace] = schema

    def lookup_path(self, path):
        components = path.split("/")
        elem = self.__parsed_doc
        for c in components:
            elem = elem[c]
        return elem

    def _parse_complex(self, xml):
        children = {}
        if len(xml.attrib):
            attribs = {}
            for k,v in xml.attrib.iteritems():
                attribs[k] = v
            children[":attributes:"] = attribs
        for e in xml:
            if isinstance(e, etree._Comment):
                continue
            ns, child_tag = decodeTag(e.tag)
            if ns not in self.parserMaps.keys():
                other = children.get("other")
                if other is None:
                    other = []
                    children["other"] = other
                other.append(e)#self._parse(e))
            else:
                mapping = children.get(child_tag)
                if mapping is not None and isinstance(mapping, list):
                    mapping.extend(self._parse(e))
                else:
                    children[child_tag] = self._parse(e)
        return children

    def validate(self, xml):
        ns, tag = decodeTag(xml.tag)
        schema = self._schemaMap.get(ns)
        if schema is not None:
            print >>sys.stderr, "validating", xml.tag
            try:
                schema.assertValid(xml)
            except Exception, e:
                raise

    def parse(self, xml):
        # validate the document before parsing
        self.parsedDoc = {decodeTag(xml.tag)[1] : self._parse(xml)}
        return self.parsedDoc

    def _parse(self, xml_elem):
        self.validate(xml_elem)
        ns, tag = decodeTag(xml_elem.tag)
        # get the parser map
        parser_map = self.parserMaps.get(ns)
        if parser_map is None:
            # cannot find a suitable parsermap
            return xml_elem
        parser = parser_map.get(tag, parser_map[self.DEFAULT_PARSER])
        return parser(xml_elem)

    def _parse_elem_array(self, xml):
        return [self._parse(xml[0])]
    def _parse_text_array(self, xml):
        return [(xml.text or "")]
    def _parse_normative_text_array(self, xml):
        return [self._parse_normative_text(xml)]
    def _parse_text(self, xml):
        return xml.text or ""
    def _parse_normative_text(self, xml):
        return self._parse_text(xml).strip()
    def _parse_uri(self, xml):
        return self._parse_text(xml)
    def _parse_complex_array(self, xml):
        return [self._parse_complex(xml)]
    def _parse_range(self, xml):
        return RangeValue.from_xml(xml)
    def _parse_bool(self, xml):
        val = (xml.text or "").strip().lower()
        if val in ("true", "1"):
            return True
        elif val in ("false", "0"):
            return False
        else:
            raise ValueError("illegal value for bool", val)
    def _parse_filesystem(self, xml):
        # if the filesystem has a 'name' attribute, remember it
        name = xml.attrib.get("name")
        if name is not None:
            self._fileSystems[name] = self._parse_complex_array(xml)
        return self._parse_complex_array(xml)

    def _parse_integer(self, xml):
        return int(xml.text)
    def _parse_unsigned_integer(self, xml):
        i = self._parse_integer(xml)
        if i < 0:
            raise ValueError("nonNegativeInteger expected", i)
        return i

    def _parse_hash(self, xml):
        algo = xml.attrib.get("algorithm", "sha1").lower()
        hexdigest = self._parse_normative_text(xml)
        return HashValidator(hexdigest, algo)

    def _parse_posix_text_array(self, xml):
        # return a tuple (filesystemName attribute, xml.text)
        return [self._parse_posix_text(xml)]
    def _parse_posix_text(self, xml):
        return ((xml.text or "").strip(), dict(xml.attrib))

    def _parse_xsdl_argument(self, xml):
        val = self._parse_normative_text(xml)
        key = xml.attrib.get("name")
        if key is not None:
            return ["%s=%s" % (key, val)]
        else:
            return ["%s" % val]

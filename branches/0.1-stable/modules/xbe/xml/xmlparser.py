#!/usr/bin/env python
"""A module, that provides a XML parser.

This is a *premature hack*. One should refactor it into a generic
parser frame-work to which an application can attach more
functionality. But I did not have time to that refactoring yet.
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging, hashlib, sys, os, os.path, time, tempfile
log = logging.getLogger(__name__)

from lxml import etree
from xbe.xml.namespaces import *
from xbe.xml import errcode

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

    def hexdigest(self):
        """Return the hexdigest."""
        return self.__hexdigest

    def algorithm(self):
        """Return the used algorithm (as string)."""
        return self.__algorithm
    
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

class Decompressor:
    """Represent a decompression algorithm.

    Its only defined method is 'decompress' which accepts source and
    destination paths. It uses the stored decompression algorithm.
       * bzip2
       * gzip
       * tbz -> bzip2 compressed tar archive
       * tgz -> gzip compressed tar archive
    """
    def __init__(self, format):
        self.__format = format

    def __repr__(self):
        return "<"+self.__class__.__name__+" using "+self.__format+">"

    def format(self):
        """Return the used compression format."""
        return self.__format

    def decompress(self, file_name, dst_dir=None, remove_original=True):
        """Decompress the src using the stored algorithm to dst.

        if dst is None src is decompressed to the same directory as
        src.
        """
        if dst_dir is None:
            dst_dir = os.path.dirname(file_name)
        start = time.time()
        log.debug("decompressing '%s' to '%s'" % (file_name, dst_dir))
        if self.format() in ('tbz', 'tgz'):
            import tarfile
            tar_file = tarfile.open(file_name)
            tar_file.extractall(dst_dir)
            log.debug("decompression took %.2fs" % (time.time() - start))

            if remove_original:
                # decompression successful, remove the original file
                log.debug("removing %s" % (file_name))
                os.unlink(file_name)
        elif self.format() == "bzip2":
            import bz2
            bz2_file = bz2.BZ2File(file_name)
            # decompress to temporary file
            tmp_file_fd, tmp_path = tempfile.mkstemp(dir=dst_dir)
            tmp_file = os.fdopen(tmp_file_fd, 'w')
            try:
                tmp_file.write(bz2_file.read())
            except Exception, e:
                raise
            finally:
                bz2_file.close()
                tmp_file.close()
            # decompression successful, rename the file
            try:
                open(file_name, 'wb').write(open(tmp_path).read())
            finally:
                os.unlink(tmp_path)
        elif self.format() == "gzip":
            import gzip
            gzip_file = gzip.GzipFile(file_name)
            # decompress to temporary file
            tmp_file_fd, tmp_path = tempfile.mkstemp(dir=dst_dir)
            tmp_file = os.fdopen(tmp_file_fd, 'w')
            try:
                tmp_file.write(gzip_file.read())
            except Exception, e:
                raise
            finally:
                gzip_file.close()
                tmp_file.close()
            # decompression successful, rename the file
            try:
                open(file_name, 'wb').write(open(tmp_path).read())
            finally:
                os.unlink(tmp_path)
        else:
            raise NotImplementedError(
                "decompression for this format is not yet implemented", self.__format
            )

    def __call__(self, src, dst):
        return self.decompress(src, dst)
        
class XMLParser:
    DEFAULT_PARSER=()
    
    def __init__(self):
        self._schema = {}          # maps from namespace to a XMLSchema
        self._parserMaps = {}      # maps from namespace to a special 'parser' map

    def register_schema(self, namespace, schema):
        self._schema[namespace] = schema
    def get_schema(self, namespace):
        return self._schema[namespace]
    def register_parserMap(self, namespace, parserMap):
        self._parserMaps[namespace] = parserMap
    def get_parser_map(self, namespace):
        return self._parserMaps.get(namespace)

    def lookup_path(self, path):
        components = path.split("/")
        elem = self.parsedDoc
        for c in components:
            elem = elem[c]
        return elem

    def _parse_complex(self, xml, *args, **kw):
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
            parserMap = self.get_parser_map(ns)
            if parserMap is None:
                other = children.get("other")
                if other is None:
                    other = []
                    children["other"] = other
                other.append(e)
            else:
                mapping = children.get(child_tag)
                if mapping is not None and isinstance(mapping, list):
                    mapping.extend(self._parse(e))
                else:
                    children[child_tag] = self._parse(e)
        return children

    def validate(self, xml):
        ns, tag = decodeTag(xml.tag)
        schema = self.get_schema(ns)
        if schema is not None:
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
        parser_map = self.get_parser_map(ns)
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

    def _parse_creation_flag(self, xml):
        return JSDL_CreationFlagEnumeration[xml.text.strip()]

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
    def _parse_compression(self, xml):
        algo = xml.attrib.get("algorithm").lower()
        return Decompressor(algo)

    def _parse_posix_text_array(self, xml):
        return [self._parse_posix_text(xml)]
    def _parse_posix_text(self, xml):
        return ((xml.text or "").strip(), xml.attrib.get("filesystemName"))

    def _parse_xsdl_argument(self, xml):
        val = self._parse_normative_text(xml)
        key = xml.attrib.get("name")
        if key is not None:
            return ["%s=%s" % (key, val)]
        else:
            return ["%s" % val]

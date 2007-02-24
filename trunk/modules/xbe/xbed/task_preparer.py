"""A class that is able to do preparation stuff for a task.

* retrieve necessary files
* unpack packages
* validate hash values
* stage-in files into an image
"""

import logging
log = logging.getLogger(__name__)

from xbe.xml.jsdl import JsdlDocument
from lxml import etree, XMLSchema

class ValidationError(ValueError):
    pass

class Preparer(object):
    def __init__(self, spool_path, jsdl, jsdl_schema):
        self.__jsdl_schema = jsdl_schema
        self.__jsdl_xml = jsdl
        self.__spool_path = spool_path
        
    def validate(self):
        try:
            self.__jdoc = JsdlDocument(self.__jsdl_schema)
            self.__parsed_jsdl = jdoc.parse(self.__jsdl_xml)
        except Exception, e:
            log.warn("could not parse the jsdl document", e)
            raise ValidationError("validation failed", e)

        # simply check for required elements
        

    def prepare(self):
        self.validate()

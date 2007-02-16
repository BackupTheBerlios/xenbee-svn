"""The xml module."""

from lxml import etree

def cloneDocument(doc):
    return etree.fromstring(etree.tostring(doc))

__all__ = [ "cloneDocument" ]

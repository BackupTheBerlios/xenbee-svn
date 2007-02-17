"""The xml module."""

from lxml import etree
import copy

def cloneDocument(doc):
    return copy.deepcopy(doc)

__all__ = [ "cloneDocument" ]

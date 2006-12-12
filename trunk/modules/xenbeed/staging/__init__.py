"""
	The staging module
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

from DataStager import DataStager, TempFile
from test_DataStager import suite as TestSuite

__all__ = [ DataStager, TempFile, TestSuite ]

#!/usr/bin/python

"""Runs self-tests for each component."""

__version__ = "$Rev$"
__author__ = "$Author$"

import unittest, os, sys

# components
import xenbeed

def suite():
    suites = []
    suites.append(xenbeed.TestSuite())
    return unittest.TestSuite(suites)

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

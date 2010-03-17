# XenBEE is a software that provides execution of applications
# in self-contained virtual disk images on a remote host featuring
# the Xen hypervisor.
#
# Copyright (C) 2007 Alexander Petry <petry@itwm.fhg.de>.
# This file is part of XenBEE.

# XenBEE is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# XenBEE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA

"""
The Xen Based Execution Environment XML Messages
"""

__version__ = "$Rev: 515 $"
__author__ = "$Author: petry $"

import logging
log = logging.getLogger(__name__)

from time import gmtime, strftime
from lxml import etree
from twisted.internet import defer, threads
from twisted.python import failure
from xbe.xml import message

from xbe.xml.namespaces import *

class XenBEEMessage(object):
    """Encapsulates a xml message."""
    def __init__(self, namespace=XSDL_NS, prefix="xsdl"):
        """Initialize a XML message using the given namespace and prefix."""
        self.__ns = NS(namespace)
        self.__prefix = prefix
        self.root = etree.Element(self.__ns("Message"), nsmap={ prefix: namespace})

    def createElement(self, tag, parent=None, text=None):
        """Utility function to create a new element for this message."""
        if parent == None: parent = self.root
        e = etree.SubElement(parent, self.__ns(tag))
        if text != None:
            e.text = str(text)
        return e

    def __str__(self):
        return etree.tostring(self.root)

    def to_s(self):
        return str(self)
    def as_xml(self):
        return self.root

class XenBEEClientMessage(XenBEEMessage):
    pass

class XenBEEStatusMessage(XenBEEClientMessage):
    """Encapsulates the status of all known tasks.

    <StatusList>
        <Status>
           <ID></ID>
           <User></User>
           <Memory></Memory>
           <CPUTime></CPUTime>
           <StartTime></StartTime>
           <EndTime></EndTime>
           <State></State>
        </Status>
        <Status>

        </Status>
    </StatusList>

    """

    def __init__(self):
        XenBEEClientMessage.__init__(self)
        self.statusList = self.createElement("StatusList", self.root)

    def addStatusForTask(self, task):
        status = self.createElement("Status", self.statusList)

        try:
            info = task.inst.getInfo()
        except:
            info = None
        
        def _c(name, txt):
            self.createElement(name, status, str(txt))
        _c("ID", task.ID())
        _c("User", "N/A")
        _c("Submitted", str(task.tstamp))
        if info:
            _c("Memory", info.memory)
            _c("CPUTime", info.cpuTime)
            if len(info.ips):
                _c("IP", info.ips[0])
            else:
                _c("IP", 'n/a')
            _c("FQDN", info.fqdn)
        else:
            _c("Memory", "N/A")
            _c("CPUTime", "N/A")
            _c("IP", 'n/a')
            _c("FQDN", 'n/a')
        if hasattr(task, "startTime"):
            _c("StartTime", str(task.startTime))
        else:
            _c("StartTime", "N/A")
        if hasattr(task, "endTime"):
            _c("EndTime", str(task.endTime))
        else:
            _c("EndTime", "N/A")
        _c("State", task.state())
        if hasattr(task, "exitCode"):
            _c("ExitCode", str(task.exitCode))
        else:
            _c("ExitCode", "N/A")

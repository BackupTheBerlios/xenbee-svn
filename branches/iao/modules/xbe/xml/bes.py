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
A module, that transforms XBE task states to a BES document
"""

__version__ = "$Rev: 515 $"
__author__ = "$Author: petry $"

import logging
log = logging.getLogger(__name__)

from lxml import etree
from xbe.xml.namespaces import *
from xbe.xml import errcode

__DefaultSubStateMap = {
    "Reserved": (CALANA_STATE, None),
    "Confirmed": (CALANA_STATE, None),
    "Stage-In": (CALANA_STATE, None),
    "Instance-Starting": (XBE, None),
    "Executing": (CALANA_STATE, None),
    "Instance-Stopping": (XBE, None),
    "Stage-Out": (CALANA_STATE, None)
    }

__BES_States = ("Pending",
                "Failed",
                "Terminated",
                "Running",
                "Finished")

def fromXBETaskState(state, separator=":", sub_text=None, substateMap=__DefaultSubStateMap):
    """Return the BES representation of state.

    @param state the string representation of a XBE task. The string
    contains of a colon separated state-pair, e.g. Running:Reserved
    would mean, that the task is currently in the BES 'Running' state
    and in the sub-state 'Reserved'. That means only *one substate* is
    allowed for now.

    @param substateMap defines a mapping from sub-state to a Namespace
    object and an optional tag that shall be used (else the sub-state
    will be used as the tag), so sub-states can be represented in
    their corrent namespace.
    
    raises ValueError if state could not be transformed
    """
    # split up the state
    state_parts = state.split(separator, 1)

    bes_state = state_parts.pop(0)
    if bes_state not in __BES_States:
        raise ValueError("illegal BES ActivityState", bes_state)
    
    sub_state = len(state_parts) and state_parts.pop() or None
    del state_parts

    bes_elem = etree.Element(BES_ACTIVITY("ActivityStatus"),
                             state=bes_state,
                             nsmap={"bes": str(BES_ACTIVITY)})

    if sub_state is not None:
        # map the sub-state to its namespace and tag
        try:
            sub_ns, tag = substateMap.get(sub_state)
            tag = tag or sub_state
        except ValueError:
            raise ValueError("namespace mapping missing", sub_state)
        etree.SubElement(bes_elem, sub_ns(tag)).text = sub_text
    return bes_elem

def toXBETaskState(bes_elem, separator=":"):
    """Transforms a BES ActivityState back into the XBE task state."""
    if bes_elem is None or bes_elem.tag != BES_ACTIVITY("ActivityStatus"):
        raise ValueError("no bes:ActivityStatus element", bes_elem)
    bes_state = bes_elem.attrib["state"]
    if bes_state not in __BES_States:
        raise ValueError("illegal BES ActivityState", bes_state)

    states = [bes_state]
    # get the sub-state
    if len(bes_elem) > 0:
        states.append(decodeTag(bes_elem[0].tag)[1])
    return separator.join(states)

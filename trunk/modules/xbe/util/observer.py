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

"""Implements the Observer pattern."""

class Observable:
    def __init__(self):
        self.__observers = []

    def addObserver(self, observer, *args, **kw):
        if not callable(observer):
            raise ValueError("observer must be callable", observer)
        self.__observers.append( (observer, args, kw) )

    def removeObserver(self, observer):
        for o_tuple in self.__observers:
            if o_tuple[0] == observer:
                self.__obserservers.remove(o_tuple)
                return
        raise LookupError("no such observer", observer)

    def notify(self, arg):
        for o, args, kw in self.__observers:
            o(arg, *args, **kw)

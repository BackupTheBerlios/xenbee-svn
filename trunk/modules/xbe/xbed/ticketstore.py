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

"""A module that holds a ticket store."""

from xbe.util import singleton, uuid

class Ticket:
    def __init__(self, id):
        self.__id = id
    def id(self):
        return self.__id

class TicketStore(singleton.Singleton):
    def __init__(self):
        singleton.Singleton.__init__(self)
        self.__tickets = {}

    def new(self):
        _id = uuid.uuid()
        ticket = Ticket(uuid.uuid())
        self.__tickets[ticket.id()] = ticket
        return ticket

    def release(self, ticket):
        if isinstance(ticket, Ticket):
            self.__tickets.pop(ticket.id())
        else:
            self.__tickets.pop(ticket)

    def lookup(self, id):
        return self.__tickets.get(id)
    
    def is_valid(self, id):
        return id in self.__tickets

    def all(self):
	return self.__tickets

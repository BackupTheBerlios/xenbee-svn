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

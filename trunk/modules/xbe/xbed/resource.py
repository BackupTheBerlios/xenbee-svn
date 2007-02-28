"""
A module used to gather resources for some task.
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging, time
log = logging.getLogger(__name__)

import threading
from twisted.internet import threads, defer
from twisted.python import failure

class ResourceGatherer(object):
    """I gather several resources for a given task.

    The gathering process can explicitly stopped by the user or due to
    some failure.
    """
    pass

class PoolException(Exception):
    pass
class PoolEmpty(PoolException):
    pass
class ItemNotInUse(PoolException):
    pass
class ItemInUse(PoolException):
    pass
class UnknownItem(PoolException):
    pass
class ItemNotAllowed(PoolException, ValueError):
    pass

class _Item:
    FREE = 0
    USED = 1
    
    def __init__(self, obj, status=FREE):
        self.obj = obj
        self.status = status
    def is_free(self):
        return self.status == _Item.FREE
    def __str__(self):
        return self.is_free() and "free" or "used"
    def __repr__(self):
        return str(self)

class Pool(object):
    """A generic pool for any kind of object.

    methods defined:
       * free() -> int
       * acquire() -> object
       * release(obj) -> None
       * add(obj) -> None
       * remove(obj) -> obj
    """

    def __init__(self):
        """initialize the pool."""
        self.__mtx = threading.RLock()
        self.__pool = {}
        self.__pending = []

    def __get_free_items(self):
        return filter(lambda i: i.is_free(), self.__pool.values())

    def __len__(self):
        """return the size of the pool."""
        return len(self.__pool)

    def __str__(self):
        """print the pool entries and their current status."""
        from pprint import pformat
        return pformat(self.__pool)
    
    def free(self):
        """ free() -> int

        return the number of free elements.
        """
        try:
            self.__mtx.acquire()
            rv = len(self.__get_free_items())
        finally:
            self.__mtx.release()
        return rv

    def acquire(self):
        """ acquire() -> item

        take some element from the pool and mark it as used. If the
        pool is empty and no item gets added, the Deferred will never
        be called back!
        
        @return defer.Deferred that is called back with the acquired item.
        """
        try:
            self.__mtx.acquire()
            free_items = self.__get_free_items()
            if len(free_items) > 0:
                # take a free one
                item = free_items.pop()
                item.status = _Item.USED
                deferred = defer.succeed(item.obj)
            else:
                # remember the request
                deferred = defer.Deferred()
                self.__pending.append(deferred)
        finally:
            self.__mtx.release()
        return deferred

    def release(self, obj):
        """ release(obj) -> None
        give an item back

        raises UnknownItem if the item does not belong to this pool
        """
        try:
            self.__mtx.acquire()
            if obj not in self.__pool.keys():
                raise UnknownItem("cant release unknown item", obj)

            assert not self.__pool[obj].is_free()
            # if there  are pending requests,  take the first  one and
            # give him the object
            try:
                deferred = self.__pending.pop()
            except IndexError:
                # mark the item as FREE again
                assert self.__pool[obj].status == _Item.USED
                self.__pool[obj].status = _Item.FREE
            else:
                # object is again (or still) in use
                deferred.callback(obj)
        finally:
            self.__mtx.release()

    def add(self, obj):
        """ add(obj) -> None
        
        add an item to the pool
        """
        try:
            self.__mtx.acquire()
            if obj in self.__pool.keys():
                raise PoolException("i already have that item", obj)
            # create a  new item,  that is USED.  In this way,  we can
            # reuse the 'release' method to handle pending requests.
            item = _Item(obj, _Item.USED)
            self.__pool[obj] = item
            self.release(obj)
        finally:
            self.__mtx.release()
        pass

    def remove(self, obj):
        """ remove(obj) -> obj
        remove an object
        
        raises UnknownItem if the object does not belong to the pool
        """
        try:
            self.__mtx.acquire()
            if obj not in self.__pool.keys():
                raise UnknownItem("I don't know that object!", obj)
            item = self.__pool[obj]
            if not item.is_free():
                raise ItemInUse("attempted to remove an item that is still in use", obj)
            self.__pool.pop(obj)
            del item
        finally:
            self.__mtx.release()
        return obj

def null_validator(obj):
    """does not do any validation."""
    return True
def string_validator(obj):
    """an example validator, that only allows strings to be added."""
    if not isinstance(obj, basestring):
        raise ValueError("obj must be string")
    return True
    
class ValidatingPool(Pool):
    """A pool, that uses a validator to check every item that wants to
    be added."""

    def __init__(self, validator=null_validator, *args, **kw):
        """initialize the validating pool.

        @param validator can be any python callable that gets passed
        the object in question as its first argument.

        if the validator raises an exception or does not return True,
        the item is not allowed to be added.
        """
        Pool.__init__(self)
        self.__validator = validator
        self.__validatorArgs = args
        self.__validatorKwArgs = kw
    
    def add(self, obj):
        """adds the object to the pool.

        raises ItemNotAllowed when the validator raises an exception
        or did not return True

        ItemNotAllowed.args will be the object in question and the
        triggering exception.
        """
        # validate the object
        try:
            if self.__validator(obj,
                                *self.__validatorArgs,
                                **self.__validatorKwArgs) is not True:
                raise ValueError("validator did not return True")
        except Exception, e:
            raise ItemNotAllowed(obj, e)
        return Pool.add(self, obj)

import re
__mac_pattern = r"^([0-9a-f]{1,2}:){5}[0-9a-f]{1,2}$"
__mac_matcher = re.compile(__mac_pattern)
del re

def mac_validator(mac):
    """The mac validator used by the MacAddressPool.

    a valid object matches this regex:
       "^([0-9a-f]{1,2}:){5}[0-9a-f]{1,2}$"
    """
    if not __mac_matcher.match(mac):
        raise ValueError("invalid mac", mac)
    return True

class MacAddressPool(ValidatingPool):
    """A pool of MAC-Addresses.

    it is just a convenience wrapper around a ValidatingPool with a
    mac_validator.
      
    allowed MAC addresses must match the following regex:
            "^([0-9a-f]{1,2}:){5}[0-9a-f]{1,2}$"

    defines a from_file classmethod that reads in a list of
    mac-addresses from a file.
    """
    def __init__(self):
        ValidatingPool.__init__(self, mac_validator)

    def from_file(cls, file):
        """reads a file which contains a list of mac addresses (each
        on a single line).

        Format:
          # MAC Address    
          01-02-03-ab-cd-ef # some comment

        comments are stripped.
        """
        pool = cls()
        if isinstance(file, basestring):
            f = open(file)
        else:
            f = file
        for line in f.readlines():
            mac = line.split("#", 1)[0].strip().lower()
            if len(mac):
                pool.add(mac)
        return pool
    from_file = classmethod(from_file)

def mac_ip_validator(mac_ip):
    return mac_validator(mac_ip[0])

class MacIPAddressPool(ValidatingPool):
    """A pool of MAC-Addresses paired with an IP address.

    it is just a convenience wrapper around a ValidatingPool with a
    mac_ip_validator.
      
    allowed MAC addresses must match the following regex:
            "^([0-9a-f]{1,2}:){5}[0-9a-f]{1,2}$"

    defines a from_file classmethod that reads in a list of
    mac-addresses paired with an IP from a file.
    """
    def __init__(self):
        ValidatingPool.__init__(self, mac_ip_validator)

    def from_file(cls, file):
        """reads a file which contains a list of mac addresses (each
        on a single line).

        Format:
          # MAC Address      IP Address
          01-02-03-ab-cd-ef  127.0.0.1    # some comment

        comments are stripped.
        """
        pool = cls()
        if isinstance(file, basestring):
            f = open(file)
        else:
            f = file
        for line in f.readlines():
            line = line.split("#", 1)[0].strip().lower()
            if len(line):
                mac, ip = line.split()
                pool.add((mac,ip))
        return pool
    from_file = classmethod(from_file)

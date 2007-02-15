"""
The Xen Based Execution Environment - Chache implementation
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging, os, os.path, threading
log = logging.getLogger(__name__)

from xbe.util.uuid import uuid
from xbe.util.database import dbapi
from twisted.internet import defer
from twisted.python import failure
from twisted.enterprise.adbapi import ConnectionPool

class CacheException(Exception):
    pass

class InvalidTypeException(CacheException):
    pass

class PermissionDenied(CacheException):
    pass

class Cache(object):
    """A `cache' that stores images and other files (kernel, initrd).

    The cache uses a specific spool directory and a database which
    holds fast lookup information (type of data).

    The stored files are annotated with information provided by the
    user himself, such as the type of the file (image, kernel, initrd,
    etc.) and more specific information like operating system, exact
    version.

    """

    def __init__(self, cache_dir):
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        else:
            import stat
            if not stat.S_ISDIR(os.stat(cache_dir)[stat.ST_MODE]):
                raise RuntimeError("`%s' already exists and does not seem to be a directory!" % _dir)
        self.__cacheDir = cache_dir
        self.__db = ConnectionPool("pysqlite2.dbapi2", os.path.join(cache_dir, "cache.db"))

    def __initTables(self, transaction):
        try:
            # create table here
            #
            #  id (pkey)    | uuid    | type | description | uri
            transaction.execute("""
            CREATE TABLE files (
               uuid varchar NOT NULL,
               type varchar NOT NULL DEFAULT "data",
               uri varchar NOT NULL,
               description varchar DEFAULT "",
               hash varchar DEFAULT "",
               primary key (uuid)
            )""")
            log.info("table 'files' has been created.")
        except Exception, e:
            log.debug(e)
        return True

    def initializeDatabase(self):
        return self.__db.runInteraction(self.__initTables)

#        # log statistics
#        sb = [ "",
#               "Cache statistics",
#               "================",
#               "" ]
#        for type,stat in self.getTypeStatistics("image", "kernel", "initrd", "data").iteritems():
#            sb.append("%s:" % (type))
#            for k, v in stat.iteritems():
#                sb.append("\t%s: %s" % (k, v))
#        log.info("\n".join(sb))
#
#    def getTypeStatistics(self, *types):
#        stats = {}
#        for t in types:
#            s = {}
#            s["entries"] = self.__getNumEntries(t)
#            stats[t] = s
#        return stats
#
#    def __getNumEntries(self, type):
#        cur = self.__db.cursor()
#        cur.execute("SELECT COUNT(*) FROM files WHERE type = ?", (type,))
#        return cur.fetchone()[0]

    def cache(self, uri, type="data", description="", meta={}, **kw):
        """Retrieve the given uri and cache it."""
        log.debug("caching URI %s" % uri)
        try:
            m = getattr(self, "cache_%s" % (type))
        except AttributeError, ae:
            return defer.fail(failure.Failure(InvalidTypeException(type)))
        try:
            meta.update(kw)
            meta["description"] = description
            return m(uri, **meta)
        except Exception, e:
            return defer.fail(failure.Failure(e))

    def getEntries(self):
        return self.__db.runQuery("SELECT uuid, type, description FROM files")

    def remove(self, entry, cred=None):
        """Remove a given entry from the cache.

        returns True, if successfully removed.

        """
        # TODO: check credentials for permission
        if not self.__operationAllowed('remove', entry, cred):
            return defer.fail(failure.Failure(
                PermissionDenied("not allowed to remove entry %s" % entry)))
        
        return self.__db.runOperation("DELETE FROM files WHERE uuid = ?", (entry,))

    def lookupByUUID(self, uuid):
        def __buildURI(rows):
            if not len(rows):
                raise LookupError("no cache entry found for uuid: %s" % (uuid,))
            path = self.__buildFileName(rows[0][0])
            return "file://" + path
        return self.__lookup("uuid = ?", (uuid,)).addCallback(__buildURI)
        
    def lookupByType(self, type):
        def __buildTypes(rows):
            return [x[0] for x in rows]
        return self.__lookup("type = ?", type).addCallback(__buildTypes)

    def __lookup(self, where_clause, *args):
        return self.__db.runQuery("SELECT uuid FROM files WHERE %s" % (where_clause), *args)

    def __operationAllowed(self, operation, entry, cred):
        log.info("TODO: implement credentials")
        return True

    def __cache_helper(self, uri, type, **meta_info):
        uid = uuid()
        dst = self.__buildFileName(uid)

        # the following sequence does the following:
        #     - use a DataStager to retrieve the uri (returns 'dst' path)
        #     - after that, compute a hash value for the dst (returns (path, hash) tuple)
        #     - transform 'dst' into a local file uri (returns (uri, hash))
        #     - insert into the DB
        # the function returns a Deferred which fires the 'uuid' of the entry
        return self.__retrieveFile(uri, dst)\
               .addCallback(self.__cb_computeHash)\
               .addCallback(lambda ph: ("file://"+ph[0], ph[1]))\
               .addCallback(self.__cb_insertEntry, uid, type, **meta_info)\
               .addCallback(lambda _: uid)\
               .addErrback(self.__cb_cleanUpFileOnError, dst)

    def __cb_cleanUpFileOnError(self, err, dst):
        log.error("something went wrong: %s" % (err.getErrorMessage()))
        # remove the file from the cache directory
        directory = os.path.dirname(dst)
        log.info("removing cache entry from filesystem: %s" % (directory))
        from xbe.util import removeDirCompletely as rm_rf
        rm_rf(directory)
        return err

    def __cb_computeHash(self, path):
        import hashlib
        algo = hashlib.sha1()
        algo.update(open(path).read())
        return (path, algo.hexdigest())

    def __cb_insertEntry(self, uri_hash, uid, type, **meta_info):
        return self.__db.runOperation("""\
            INSERT INTO files (uuid, type, uri, hash, description)
                    VALUES (?, ?, ?, ?, ?)""", (uid,
                                                type,
                                                uri_hash[0],
                                                uri_hash[1],
                                                meta_info["description"]))

    def cache_data(self, uri, **meta_info):
        return self.__cache_helper(uri, "data", **meta_info)
    def cache_image(self, uri, **meta_info):
        return self.__cache_helper(uri, "image", **meta_info)
    def cache_kernel(self, uri, **meta_info):
        return self.__cache_helper(uri, "kernel", **meta_info)
    def cache_initrd(self, uri, **meta_info):
        return self.__cache_helper(uri, "initrd", **meta_info)

    def __buildFileName(self, uid):
        dst = os.path.join(self.__cacheDir, uid)
        dst = os.path.join(dst, "data")
        return dst

    def __retrieveFile(self, uri, dst):
        from xbe.util.staging import DataStager
        ds = DataStager(uri, dst)
        return ds.perform()

"""
A class that can be used to stage data from a source to a destination.

    Examples protocols are:
	* http, ftp, file
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

import pycurl, os, os.path, logging, time
log = logging.getLogger(__name__)

import threading
from twisted.internet import threads, defer
from twisted.python import failure

from xbe.util.exceptions import XenBeeException
try:
    from traceback import format_exc as format_exception
except:
    from traceback import format_exception

class StagingError(XenBeeException):
    pass

class StagingAborted(StagingError):
    pass

class DataStager:
    def __init__(self, src, dst):
	"""Initializes the DataStager.

	src - source from which to retrieve the data
	dst - destination to which the data is to be transfered
	"""
	self.src = src.encode("ascii")
	self.dst = dst.encode("ascii")
        self.tmpdst = None
        self._abort = False

        __tmp = "abcdefghijklmnopqrstuvwxyz"
        self.__charList = [ c for c in "0123456789" + __tmp + __tmp.upper() ]
        
        self.curl = pycurl.Curl()
        self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
	self.curl.setopt(pycurl.CONNECTTIMEOUT, 30)
	self.curl.setopt(pycurl.TIMEOUT, 300)
	self.curl.setopt(pycurl.NOSIGNAL, 1)
	self.curl.setopt(pycurl.VERBOSE, 0)

    def __call__(self):
	return self.perform()

    def __str__(self):
        return "'%s' => '%s'" % (self.src, self.dst)

    def _write(self, buf):
        if self.aborted():
            # TODO: remove file here?
            return 0
        self.fp.write(buf)

    def _read(self, size):
        if self.aborted():
            return 0
        return self.fp.read(size)

    def cleanUp(self):
        if self.tmpdst and os.path.exists(self.tmpdst):
            os.unlink(self.tmpdst)
            self.tmpdst = None

    def abort(self):
        self._abort = True
    def aborted(self):
        return self._abort

    def __tempFileName(self):
        import random
        __ext = "".join([random.choice(self.__charList) for i in xrange(6)])
        tmp = "." + os.path.basename(self.dst) + "." + __ext
        tmp = os.path.join(os.path.dirname(self.dst), tmp)
        return tmp
        
        
    def perform_download(self):
        """Download the file from src to dest."""
        self.tmpdst = self.__tempFileName()
	self.curl.setopt(pycurl.URL, self.src)
        self.curl.setopt(pycurl.WRITEFUNCTION, self._write)

	try:
	    log.debug("beginning retrieving uri: %s" % self.src)
	    start = time.time()

            directory = os.path.dirname(self.tmpdst)
            if not os.path.exists(directory):
                os.makedirs(directory)
        
            self.fp = open(self.tmpdst, "wb")
	    self.curl.perform()
            self.fp.close()
            self.curl.close()
	    self.duration = time.time() - start

            os.rename(self.tmpdst, self.dst)
            self.tmpdst = None
            
	    log.debug("finished retrieving uri: %s: %ds" % (self.src, self.duration))
	except Exception, e:
	    log.error("retrieval failed: %s" % str(e))
            raise
        return self.dst

    def perform_upload(self):
        self.fp = open(self.src, 'rb')
	self.curl.setopt(pycurl.URL, self.dst)
        self.curl.setopt(pycurl.UPLOAD, 1)
	self.curl.setopt(pycurl.READFUNCTION, self._read)
        self.curl.setopt(pycurl.INFILESIZE, os.path.getsize(self.src))

	try:
	    log.debug("beginning upload of: %s" % self.src)
	    start = time.time()
	    self.curl.perform()
	    dur = time.time() - start
	    log.debug("finished uploading of %s after %ds" % (self.src, dur))
	except Exception, e:
	    log.error("upload failed: %s" % str(e))
            raise
	self.curl.close()
        return self.dst

    def __perform(self):
	"""Transfers data from source to destination."""

        if self.aborted():
            raise StagingAborted("staging has been aborted")

	log.debug("staging %s" % str(self))
        from urlparse import urlparse
        (scheme, netloc, path, params, query, fragment) = urlparse(self.src)
        try:
            if scheme or not os.path.exists(self.src):
                return self.perform_download()
            else:
                return self.perform_upload()
        except Exception, e:
            log.error("could not perform staging: "+format_exception())
            self.abort()
            raise

    def perform(self, asynchronous=True):
	"""Transfers data from source to destination.

        if asynchronous: call in thread
        returns a Deferred
        """
        if asynchronous:
            self.defer = threads.deferToThread(self.__perform)
        else:
            self.defer = defer.Deferred()
            try:
                r = self.__perform()
                self.defer.callback(r)
            except:
                r = failure.Failure()
                self.defer.errback(r)
        return self.defer

class FileSetRetriever:
    """Retrieve many files and abort all if any one fails."""

    def __init__(self, files, cleanUp=True):
        """Retrieve all files in the list 'files'.

        each item consits of a URI (source) and a path (destination).

        """
        self.cleanUp = cleanUp
        self.files = files
        self.pending = [ x[1].encode('ascii') for x in self.files ]
        self.stagers = []
        self.defer = defer.Deferred()
        self.lock = threading.RLock()

    def __fileRetrieved(self, path):
        """Called when a file has been retrieved."""
        self.lock.acquire()
        log.debug("retrieved " + path)
        self.pending.remove(path)
        finished = len(self.pending) == 0
        self.lock.release()
        if finished:
            self.defer.callback(self)
            
    def __fileFailed(self, err):
        """Called when a file could not be retrieved."""
        self.lock.acquire()
        log.error("file failed: " + err.getTraceback())
        # abort all stagers
        for stager in filter(lambda s: not s.aborted(), self.stagers):
            stager.abort()
        for stager in filter(lambda s: s.aborted(), self.stagers):
            self.stagers.remove(stager)
            if self.cleanUp and os.path.exists(stager.dst):
                log.info("removing staged file: "+stager.dst)
                os.unlink(stager.dst)
        doerrback = not self.defer.called and not len(self.stagers)
        self.lock.release()
        if doerrback:
            self.defer.errback(err)
        return err

    def perform(self):
        from pprint import pformat
        log.debug("retrieving set of files:\n" + pformat(self.files))
        self.lock.acquire()
        for src,dst in self.files:
            stager = DataStager(src, dst)
            self.stagers.append(stager)
            stager.perform().addCallback(self.__fileRetrieved).addErrback(self.__fileFailed)
        self.lock.release()
        return self.defer

import stat

class TempFile:
    """Provides a temporary file that gets unlinked if no longer needed.

    WARNING: This implementation uses the os.tmpnam() function to generate
	a random file name, but this could lead to a symlink attack.

	It tries its best to avoid such an attack by verifying after
	opening whether the file is a symlink or not.

    """

    def __init__(self, keep=False):
	"""Initializes a temporary file.

	The file will be generated in the temporary folder
	defined by the operating system.

	keep -- unlink the temporary file or not.

	The tempfile will be generated using using the
	'os.tmpnam()' function. Since this function is known
	to have a symlink attack security leak, this class has
	the same drawbacks, but tries to avoid it best:

	1. check if file exists
	2. temporary file is opened for writing
	3. now is checked, if the opened file has been a symlink

	"""

	self.f = None
	self.keep = keep

	import warnings
	warnings.filterwarnings("ignore", "tmpnam", RuntimeWarning, __name__)
	self.path = os.tmpnam()
	if os.access(self.path, os.F_OK):
	    raise RuntimeError, "probable security breach while using temporary file: %s" % self.path

	try:
	    self.f = open(self.path, "wb")
	except IOError:
	    raise

	# check if it is a symlink and abort if so
	if stat.S_ISLNK(os.lstat(self.path)[stat.ST_MODE]):
	    self.f.close()
	    self.f = None
	    raise RuntimeError, "probable security breach while using temporary file: %s" % self.path

	self.write = self.f.write
	self.read  = self.f.read
	self.fileno= self.f.fileno
	self.seek  = self.f.seek
	self.encoding = self.f.encoding
	self.readlines = self.f.readlines
	self.flush = self.f.flush

    def __del__(self):
	if self.f:
	    self.f.close()
	    self.f = None
	    if not self.keep:
                import os
                os.unlink(self.path)

__all__ = [ 'DataStager', 'FileSetRetriever', 'TempFile' ]

"""
A class that can be used to stage data from a source to a destination.

    Examples protocols are:
	* http, ftp, file
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

import pycurl, threading, sys, os, logging, time
log = logging.getLogger(__name__)

__all__ = [ 'DataStager', 'TempFile' ]

class DataStager:
    def __init__(self, src, dst):
	"""Initializes the DataStager.

	src - source from which to retrieve the data
	dst - destination to which the data is to be transfered
	"""

	self.src = src.encode("ascii")
	self.dst = dst.encode("ascii")

    def __call__(self):
	self.run()

    def run(self):
	"""Transfers data from source to destination

	TODO: include upload: see /usr/share/doc/python-pycurl/examples/file_upload.py
	"""
	log.debug("staging '%s' => '%s'" % (self.src, self.dst))
	
	fp = open(self.dst, "wb") # for now assume dst is a local file
	curl = pycurl.Curl()
	curl.setopt(pycurl.URL, self.src)
	curl.setopt(pycurl.FOLLOWLOCATION, 1)
	curl.setopt(pycurl.CONNECTTIMEOUT, 30)
	curl.setopt(pycurl.TIMEOUT, 300)
	curl.setopt(pycurl.NOSIGNAL, 1)
	curl.setopt(pycurl.WRITEDATA, fp)

	try:
	    log.debug("beginning retrieving uri: %s" % self.src)
	    start = time.time()
	    curl.perform()
	    dur = time.time() - start
	    log.debug("finished retrieving uri: %s: %ds" % (self.src, dur))
	except Exception, e:
	    log.error("retrieval failed: %s" % str(e))
            raise
	curl.close()
	fp.close()

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
	except IOError, ioerr:
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
	    if not self.keep: os.unlink(self.path)


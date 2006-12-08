"""
A class that can be used to stage data from a source to a destination.

	Examples protocols are:
		* http, ftp, file
"""

import pycurl, threading, sys, os

class DataStager(threading.Thread):
	def __init__(self, src, dst):
		"""Initializes the DataStager.

		src - source from which to retrieve the data
		dst - destination to which the data is to be transfered
		"""

		threading.Thread.__init__(self)
		self.src = src
		self.dst = dst

	def __call__(self):
		self.run()

	def run(self):
		"""Transfers data from source to destination

		TODO: include upload: see /usr/share/doc/python-pycurl/examples/file_upload.py
		"""
		fp = open(self.dst, "wb") # for now assume dst is a local file
		curl = pycurl.Curl()
		curl.setopt(pycurl.URL, self.src)
		curl.setopt(pycurl.FOLLOWLOCATION, 1)
		curl.setopt(pycurl.CONNECTTIMEOUT, 30)
		curl.setopt(pycurl.TIMEOUT, 300)
		curl.setopt(pycurl.NOSIGNAL, 1)
		curl.setopt(pycurl.WRITEDATA, fp)

		try:
			curl.perform()
		except:
			import traceback
			# TODO: use twisted logging here...
			traceback.print_exc(file=sys.stderr)
			sys.stderr.flush()
		curl.close()
		fp.close()

class TempFile:
	"""Provides a temporary file that gets unlinked if no longer needed.

	WARNING: This implementation uses the os.tmpnam() function to generate
                 a random file name, but this could lead to a symlink attack.

		 It tries its best to avoid such an attack by verifying after
                 opening whether the file is a symlink or not.
	"""

	def __init__(self):
		import warnings
		warnings.filterwarnings("ignore", "tmpnam", RuntimeWarning, __name__)
		self.path = os.tmpnam()
                self.f = open(self.path, "wb")
                # check if it is a symlink and abort if so
                import stat
                if stat.S_ISLNK(os.stat(self.path)[stat.ST_MODE]):
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
			os.unlink(self.path)
			self.f = None



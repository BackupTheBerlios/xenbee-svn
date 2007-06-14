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

"""A class that is able to do preparation stuff for a task.

* retrieve necessary files
* unpack packages
* validate hash values
* stage-in files into an image
"""

import logging, os, os.path, sys, subprocess, errno, stat
log = logging.getLogger(__name__)

from zope.interface import Interface, implements
from lxml import etree
from pprint import pprint, pformat

from xbe.xml import jsdl
from xbe.util.staging import DataStager
from xbe.xbed.daemon import XBEDaemon

class ValidationError(ValueError):
    pass

class ScriptFailed(Exception):
    def __init__(self, message, script, exitcode, stdout="", stderr=""):
        Exception.__init__(self, message)
        self.exitcode = int(exitcode)
        self.script = script
        self.stdout = stdout
        self.stderr = stderr

    def __repr__(self):
        return "<%(cls)s with exitcode %(code)d>" % {
            "cls": self.__class__.__name__,
            "code":self.exitcode,
        }

class ILocationHandler(Interface):
    def can_handle(location):
        """Returns true, if the given location information can be
        handled, False otherwise."""

    def handle(self, location, target_dir, target_file_name):
        """handles the location information (i.e. download) with the
        given target."""

class URILocationHandler:
    implements(ILocationHandler)
    
    def can_handle(self, location):
        return location.get("URI") is not None

    def __transform_cache_uri_hack(self, uri):
        # XXX: this is a hack, please, think about a better way!
        try:
            xbed = XBEDaemon.getInstance()
            if not hasattr(xbed, "cache") or xbed.cache is None:
                raise ValueError("could not transform uri, no cache", uri)

            cache_id = uri.split("/")[-1]
            log.debug("looking up cache-id %s" % cache_id)

            from twisted.internet import defer
            cache_uri = defer.waitForDeferred(
                xbed.cache.lookupByUUID(cache_id)).getResult()
            return cache_uri
        except Exception, e:
            log.warn("could not look up cache entry", e)
            raise

    def handle(self, location,
               target_dir,
               target_file_name=None):
        """Handle a Location entry with an URI as its source.

        The URI is retrieved and according to additional elements
        validated (hash validation) and decompressed.
        """
        uri = location["URI"]
        if uri.startswith("cache://"):
            uri = self.__transform_cache_uri_hack(uri)
            
        # retrieve
        log.debug("retrieving: %s" % (uri))
        if target_file_name is None:
            filename = uri.split("/")[-1]
        else:
            filename = target_file_name
        dst = os.path.join(target_dir, filename)
        ds = DataStager(uri, dst)
        rv = ds.perform_download()
        log.debug("retrieved to %s" % (dst))

        # verify the hash value
        hash_validator = location.get("Hash")
        if hash_validator is not None:
            log.debug("validating data")
            if not hash_validator.validate(open(dst).read()):
                raise ValidationError("the retrieved file did not match the hash-value",
                                      uri, hash_validator.algorithm(),
                                      hash_validator.hexdigest()
                )

        # decompress the file if necessary
        compression = location.get("Compression")
        if compression is not None:
            log.debug("decompressing %s" % (dst))
            compression.decompress(file_name=dst, remove_original=True)
            

class Preparer(object):
    def __init__(self):
        """prepares necessary files for a task."""
        self.__locationHandler = [
            URILocationHandler() # the default handler
        ]

    def register_location_handler(self, handler, default=False):
        """Register a new location handler with this preparer."""
        if default:
            self.__locationHandler[0] = handler
        else:
            if handler not in self.__locationHandler:
                self.__locationHandler.append(handler)

    def prepare(self, spool_path, jsdl_doc):
        """prepare the given jsdl_doc.
        
        spool_path is the path to some directory where the files will
        be retrieved to.

        jsdl_doc is a parsed and validated JSDL document.
        """
        if not isinstance(jsdl_doc, jsdl.JsdlDocument):
            raise ValueError("jsdl_doc must be a JsdlDocument", jsdl_doc)
        if not os.path.exists(spool_path):
            raise ValueError("spool_path must exist", spool_path)
        self.__spool = spool_path

        try:
            instdesc = jsdl_doc.lookup_path("JobDefinition/JobDescription/"+
                                            "Resources/InstanceDefinition/"+
                                            "InstanceDescription")
        except Exception, e:
            raise ValidationError("could not find an InstanceDescription", e)

        # do we need to retrieve a package
        if instdesc.get("Package") is not None:
            self._prepare_package(instdesc.get("Package"))
        else:
            self._prepare_inst(instdesc.get("Instance"))

        # get optional control scripts
        if instdesc.get("Control") is not None:
            self._prepare_control_files(instdesc.get("Control"))

        # mapping from logical name to mount-point
        known_filesystems = jsdl_doc.get_file_systems()

        # now we can handle the stage in definitions
        try:
            stagings = jsdl_doc.lookup_path("JobDefinition/JobDescription/"+
                                        "DataStaging")
        except KeyError, e:
            stagings = None

        # mount the image
        from xbe.util import disk
        img = disk.mountImage(
            os.path.join(self.__spool, "image"),  # path to the image file
            fs_type=disk.FS_EXT3,                 # filesystem type
            dir=self.__spool                      # where to create the tmp mount-point
        )
        log.debug("mounted image to '%s'" % img.mount_point())

        try:
            # staging operations
            if stagings is not None:
                self._prepare_stagings(stagings,
                                       img.mount_point(),
                                       known_filesystems)

            # setup scripts
            script_dir = os.path.join(self.__spool, "scripts")
            if os.path.isdir(script_dir):
                self._call_scripts(
                    script_dir, "setup",
                    self.__spool, img.mount_point() # passed to the script
                )
        finally:
            del img

        # create swap space
        self._prepare_swap(jsdl_doc.lookup_path("JobDefinition/JobDescription/Resources"))
        
        log.info("preparation complete!")

    def _call_scripts(self, script_dir, script_prefix, *args):
        for script in filter(lambda s: s.startswith(script_prefix),
                             os.listdir(script_dir)):
            script_path = os.path.join(script_dir, script)
            log.debug("calling script '%s'" % (script_path))
            self._run_script(script_path, *args)

    def _run_script(self, script, *args):
        try:
            argv = [script]
            argv.extend(args)
            p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                raise ScriptFailed("script failed",
                                   os.path.basename(script),
                                   p.returncode,
                                   stdout, stderr)
        except OSError, e:
            raise

    def _prepare_swap(self, resources):
        from xbe.util.disk import makeSwap
        path = os.path.join(self.__spool, "swap")
        makeSwap(path, 256)
        
    def _prepare_stagings(self, stagings, img_mount_point, known_filesystems):
        log.debug("performing the staging operations")
        for staging in stagings:
            if staging.get("Source") is None:
                # stage-out operation
                continue
            creation_flag = staging["CreationFlag"]
            if creation_flag == jsdl.JSDL_CreationFlag_APPEND:
                raise ValueError("cannot currently handle *append* CreationFlag")
            
            fs = staging.get("FilesystemName")
            if fs is None:
                raise ValueError("the FilesystemName *must* be specified!")
            # lookup the file system
            mount_point = known_filesystems.get(fs)
            if mount_point is None:
                raise ValueError("the referenced FilesystemName could not be found!")
            dst_dir = os.path.join(img_mount_point, mount_point.lstrip("/"))
            dst_file = staging["FileName"]
            
            if os.path.exists(os.path.join(dst_dir, dst_file)) and \
                   creation_flag == jsdl.JSDL_CreationFlag_DONT_OVERWRITE:
                log.debug("file already exists")
                continue

            self._handle_location(staging["Source"],
                                  dst_dir=os.path.join(img_mount_point,
                                                       mount_point[1:]),
                                  dst_file=staging["FileName"])

    def _prepare_package(self, package):
        self._handle_location(package["Location"])

    def _prepare_inst(self, inst):
        log.debug("preparing from inline instance description:")

        log.debug("getting kernel...")
        self._handle_location(inst["Kernel"]["Location"], dst_file="kernel")

        if inst.get("Initrd") is not None:
            log.debug("getting initrd...")
            self._handle_location(inst["Initrd"]["Location"], dst_file="initrd")
        log.debug("getting image...")
        self._handle_location(inst["Image"]["Location"], dst_file="image")

    def _prepare_control_files(self, control):
        log.debug("preparing control files")
        script_dir = os.path.join(self.__spool, "scripts")
        try:
            os.makedirs(script_dir)
        except OSError, e:
            if e.errno == errno.EEXIST:
                pass
            else:
                raise
        counters = {}
        for script in control["Script"]:
            target = script[":attributes:"]["target"]
            counter = counters.get(target)
            if counter is None:
                counter = 0
                counters[target] = counter
            dst_file_name = "%s" % (target)
            # append a sequence number
            if counter > 0: dst_file_name += ".%d" % (counter)
            self._handle_location(script["Location"], script_dir, dst_file_name)
            # make it executable
            os.chmod(os.path.join(script_dir, dst_file_name),
                     stat.S_IEXEC | stat.S_IRUSR | stat.S_IREAD)
            counters[target] += 1

    def _handle_location(self, location, dst_dir=None, dst_file=None):
        # find a handler, that is abled to
        if dst_dir is None:
            dst_dir = self.__spool
        for h in self.__locationHandler:
            if h.can_handle(location):
                return h.handle(location, dst_dir, dst_file)
        raise ValueError("I cannot handle this location-element", location)

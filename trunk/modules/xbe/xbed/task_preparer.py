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

class ValidationError(ValueError):
    pass


class ILocationHandler(Interface):
    def can_handle(location):
        """Returns true, if the given location information can be handled, False otherwise."""

    def handle(self, location, target_dir, target_file_name):
        """handles the location information (i.e. download) with the given target."""

class URILocationHandler:
    implements(ILocationHandler)
    
    def can_handle(self, location):
        return location.get("URI") is not None

    def handle(self, location, target_dir, target_file_name=None):
        # retrieve
        uri = location["URI"]
        log.debug("retrieving: %s" % (uri))
        if target_file_name is None:
            filename = uri.split("/")[-1]
        else:
            filename = target_file_name
        dst = os.path.join(target_dir, filename)
        ds = DataStager(uri, dst)
        rv = ds.perform(asynchronous=False)
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
        """prepares necessary files for a task.

        """
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

        # now we can handle the stage in definitions
        known_filesystems = {}    # mapping from logical name to mount-point
        try:
            file_systems = jsdl_doc.lookup_path(
                "JobDefinition/JobDescription/Resources/FileSystem")
            for fs in file_systems:
                logical_name = fs[":attributes:"]["name"]
                mount_point  = fs["MountPoint"]
                known_filesystems[logical_name] = mount_point
        except Exception, e:
            log.warn('error while retrieving defined filesystems', e)
            raise
            
        if "ROOT" not in known_filesystems:
            known_filesystems["ROOT"] = "/"

        # handle the DataStaging elements
        try:
            stagings = jsdl_doc.lookup_path("JobDefinition/JobDescription/"+
                                        "DataStaging")
        except KeyError, e:
            stagings = None
        else:
            self._prepare_stagings(stagings, known_filesystems)
        self._call_scripts(os.path.join(self.__spool, "scripts"), "setup")
        log.info("preparation complete!")

    def _call_scripts(self, script_dir, script_prefix):
        from xbe.util.disk import mountImage
        image = mountImage(os.path.join(self.__spool, "image"), dir=self.__spool)
        log.debug("mounted image to '%s'" % image.mount_point())

        for script in filter(lambda s: s.startswith(script_prefix),
                             os.listdir(script_dir)):
            script_path = os.path.join(script_dir, script)
            log.debug("calling script '%s'" % (script_path))
            self._run_script(script_path, self.__spool, image.mount_point())

    def _run_script(self, script, *args):
        try:
            argv = [script]
            argv.extend(args)
            p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                raise ValueError("script failed", script, p.returncode, stdout, stderr)
            log.debug("stdout of script:\n%s" % stdout)
            log.debug("errout of script:\n%s" % stderr)
        except OSError, e:
            raise
        
    def _prepare_stagings(self, stagings, known_filesystems):
        log.debug("performing the staging operations")
        # first, mount the image
        from xbe.util.disk import mountImage
        image = mountImage(os.path.join(self.__spool, "image"), dir=self.__spool)
        log.debug("mounted image to '%s'" % image.mount_point())

        for staging in stagings:
            log.debug(pformat(staging))
            if staging.get("Source") is None:
                # stage-out operation
                log.debug("ignoring stageout operation")
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
            dst_dir = os.path.join(image.mount_point(), mount_point.lstrip("/"))
            dst_file = staging["FileName"]

            if os.path.exists(os.path.join(dst_dir, dst_file)) and \
               creation_flag == jsdl.JSDL_CreationFlag_DONT_OVERWRITE:
                log.debug("file already exists")
                continue

            self._handle_location(staging["Source"],
                                  dst_dir=os.path.join(image.mount_point(), mount_point[1:]),
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

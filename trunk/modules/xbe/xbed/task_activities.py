"""A module that describes several activities made by a task.

* retrieve necessary files
* unpack packages
* validate hash values
* stage-in files into an image
"""

import sys, signal, os, os.path, threading, subprocess, errno, stat
import logging
log = logging.getLogger(__name__)

from zope.interface import Interface, implements
from lxml import etree
from pprint import pprint, pformat

from xbe.xml import jsdl
from xbe.util.staging import DataStager, StagingError, StagingAborted
from xbe.util.activity import ThreadedActivity, ComplexActivity, ActivityProxy, IUndoable
from xbe.xbed.daemon import XBEDaemon

class ValidationError(ValueError):
    pass

class ScriptFailed(Exception):
    def __init__(self, message, script, exitcode, stderr=""):
        Exception.__init__(self, message)
        self.exitcode = int(exitcode)
        self.script = script
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

    def handle(location, *args, **kw):
        """handles the location information (i.e. download) with the
        given target."""

class StagingActivity:
    def __init__(self, activity):
        self.activity = activity

    def perform_download(self, src, dst):
        try:
            self.activity.lock()
            assert self.activity.stager is None
            self.activity.stager = DataStager(src, dst)
        finally:
            self.activity.unlock()

        try:
            rv = self.activity.stager.perform_download()
            log.debug("retrieved to %s" % (dst))
        except StagingAborted:
            return

        try:
            self.activity.lock()
            self.activity.stager = None
        finally:
            self.activity.unlock()
        return rv

    def perform_upload(self, src, dst):
        try:
            self.activity.lock()
            assert self.activity.stager is None
            self.activity.stager = DataStager(src, dst)
        finally:
            self.activity.unlock()

        try:
            rv = self.activity.stager.perform_upload()
            log.debug("uploaded %s" % (src))
        except StagingAborted:
            return

        try:
            self.activity.lock()
            self.activity.stager = None
        finally:
            self.activity.unlock()
        return rv

class URILocationHandler(StagingActivity):
    implements(ILocationHandler)

    def __init__(self, activity):
        StagingActivity.__init__(self, activity)
    
    def can_handle(self, location):
        return location.get("URI") is not None

    def __transform_cache_uri_hack(self, uri):
        # XXX: this is a hack, please, think about a better way!
        xbed = XBEDaemon.getInstance()
        if not hasattr(xbed, "cache") or xbed.cache is None:
            raise ValueError("could not transform uri, no cache", uri)
        
        cache_id = uri.split("/")[-1]
        log.debug("looking up cache-id %s" % cache_id)

        import threading
        from twisted.python import failure
        from twisted.internet import defer

        cv = threading.Condition()
        def notify(result, deferred):
            cv.acquire()
            cv.notifyAll()
            self.__result = result
            cv.release()
        d = xbed.cache.lookupByUUID(cache_id)
        d.addBoth(notify, d)

        try:
            cv.acquire()
            while not d.called:
                cv.wait(1)
        finally:
            cv.release()
            
        result = self.__result
        del self.__result
        if isinstance(result, failure.Failure):
            result.raiseException()
        return result
        
#        def cache_waiter():
#            cache_lookup = defer.waitForDeferred(xbed.cache.lookupByUUID(cache_id))
#            yield cache_lookup
#            cache_lookup = cache_lookup.getResult()
#            yield cache_lookup
#            return
#        cache_waiter = defer.deferredGenerator(cache_waiter)
#        deferred = cache_waiter()
#        result = deferred.result
#        deferred.addBoth(str).addBoth(log.debug)
#        if isinstance(result, failure.Failure):
#            result.raiseException()
#        return result

    def handle(self, location,
               dst_dir,
               dst_file=None):
        """Handle a Location entry with an URI as its source.

        The URI is retrieved and according to additional elements
        validated (hash validation) and decompressed.
        """
        uri = location["URI"]
        if uri.startswith("cache://"):
            uri = self.__transform_cache_uri_hack(uri)
            
        # retrieve
        log.debug("retrieving: %s" % (repr(uri)))
        if dst_file is None:
            filename = uri.split("/")[-1]
        else:
            filename = dst_file
        dst = os.path.join(dst_dir, filename)

        self.perform_download(uri, dst)

        if self.activity.check_abort():
            return

        # verify the hash value
        hash_validator = location.get("Hash")
        if hash_validator is not None:
            log.debug("validating data")
            if not hash_validator.validate(open(dst).read()):
                raise ValidationError("the retrieved file did not match the hash-value",
                                      uri, hash_validator.algorithm(),
                                      hash_validator.hexdigest()
                )

        if self.activity.check_abort():
            return

        # decompress the file if necessary
        compression = location.get("Compression")
        if compression is not None:
            log.debug("decompressing %s" % (dst))
            compression.decompress(file_name=dst, remove_original=True)
            

class StageOutHandler(StagingActivity):
    implements(ILocationHandler)

    def __init__(self, activity):
        StagingActivity.__init__(self, activity)
    
    def can_handle(self, ds):
        trgt = ds.get("Target")
        if trgt is not None:
            return trgt.get("URI") is not None
        return False

    def handle(self, ds, mount_point, workdir="/", file_systems={"ROOT": "/"}):
        """Handle a DataStaging entry.

        @param ds the parsed DataStaging element
        @param mount_point the path to the mounted image
        @param workdir the working directory of the task
        @param file_systems all defined filesystems (map from log.name to mount point)
        """
        directory = ds.get("FilesystemName")
        if directory is not None:
            directory = file_systems[directory]
        else:
            directory = workdir
        file_name = os.path.join(directory, ds["FileName"])
        if ds.get("Target") is not None:
            uri = ds["Target"]["URI"]
            
            log.debug("uploading: %s -> %s" % (file_name, uri))
            
            # make file relative to image mount_point
            file_name = os.path.join(mount_point, file_name.lstrip("/"))
            return self.perform_upload(file_name, uri)

class TaskActivity(ActivityProxy):
    implements(IUndoable)
    
    def __init__(self, spool):
        """prepares necessary files for a task."""
        ActivityProxy.__init__(self)
        self.ctxt = None
        self.stager = None # the current stager
        self.process = None # a currently running subprocess
        self.spool = spool
        
        self.__locationHandler = []

    def register_location_handler(self, handler, default=False):
        """Register a new location handler with this preparer."""
        self.lock()
        if default:
            self.__locationHandler[0] = handler
        else:
            if handler not in self.__locationHandler:
                self.__locationHandler.append(handler)
        self.unlock()

    def check_abort(self):
        if self.ctxt is not None:
            return self.ctxt.check_abort()
        return False

    def abort(self):
        try:
            self.lock()
            if self.stager is not None:
                self.stager.abort()
            if self.process is not None:
                try:
                    os.kill(self.process.pid, signal.SIGTERM)
                except OSError,e :
                    log.info("error while terminating subprocess", e)
                    raise
        finally:
            self.unlock()

    def __call__(self, context, jsdl_doc):
        if not isinstance(jsdl_doc, jsdl.JsdlDocument):
            raise ValueError("jsdl_doc must be a JsdlDocument", jsdl_doc)
        if not os.path.exists(self.spool):
            raise ValueError("spool_path must exist", self.spool)

        self.ctxt = context
        return self.perform(jsdl_doc)

    def perform(self, jsdl_doc):
        raise NotImplementedError("implement 'perform' in a subclass")

    def undo(self):
        raise NotImplementedError("implement 'undo' in a subclass")

    def _call_scripts(self, script_dir, script_prefix, *args):
        for script in filter(lambda s: s.startswith(script_prefix),
                             os.listdir(script_dir)):
            if self.check_abort():
                return
            script_path = os.path.join(script_dir, script)
            log.debug("calling script '%s'" % (script_path))
            self._run_script(script_path, *args)

    def _run_script(self, script, *args):
        try:
            self.lock()
            argv = [script]
            argv.extend(args)
            self.process = subprocess.Popen(argv,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            close_fds=True)
        finally:
            self.unlock()

        rc = self.process.wait()
        p = self.process
        try:
            self.lock()
            self.process = None
        finally:
            self.unlock()

        #
        # evaluate the exitcode
        #   0 - success
        #  >0 - failure
        # -15 - terminated by signal (aborted)
        #  <0 - killed by some other signal (indicate it as a failure)
        log.debug("script finished:")
        log.debug("stdout:")
        map(log.debug, [line.strip() for line in p.stdout.readlines()])
        log.debug("stderr:")
        map(log.debug, [line.strip() for line in p.stderr.readlines()])
            
        if rc == -15:
            return rc # assume aborted
        if rc > 0 or rc < 0:
            raise ScriptFailed("script failed",
                               os.path.basename(script),
                               rc, p.stderr.read())
        # else rc == 0
        return rc

    def _handle_location(self, location, *args, **kw):
        # find a handler, that is abled to
        for h in self.__locationHandler:
            if h.can_handle(location):
                return h.handle(location, *args, **kw)
        raise ValueError("I cannot handle this location-element", location)

    def _mount_image(self, img_name="image"):
        # mount the image
        from xbe.util import disk
        img = disk.mountImage(
            os.path.join(self.spool, img_name),  # path to the image file
            fs_type=disk.FS_EXT3,                # filesystem type
            dir=self.spool                       # where to create the tmp mount-point
        )
        log.debug("mounted image to '%s'" % img.mount_point())
        return img


class SetUpActivity(TaskActivity):
    def __init__(self, spool):
        """prepares necessary files for a task."""
        TaskActivity.__init__(self, spool)
        self.register_location_handler(URILocationHandler(self))

    def perform(self, jsdl_doc):
        """prepare the given jsdl_doc.
        
        spool_path is the path to some directory where the files will
        be retrieved to.

        jsdl_doc is a parsed and validated JSDL document.

        returns a ComplexActivity.
        """
        try:
            instdesc = jsdl_doc.lookup_path("JobDefinition/JobDescription/"+
                                            "Resources/InstanceDefinition/"+
                                            "InstanceDescription")
        except Exception, e:
            raise ValidationError("could not find an InstanceDescription", e)

        if self.check_abort():
            return

        ##############################################
        #
        # Retrieve a package or an inline definition
        #
        ##############################################
        if instdesc.get("Package") is not None:
            self._prepare_package(instdesc.get("Package"))
        else:
            self._prepare_inst(instdesc.get("Instance"))

        if self.check_abort():
            return

        
        ##############################################
        #
        # get the control scripts
        #
        ##############################################
        if instdesc.get("Control") is not None:
            self._prepare_control_files(instdesc.get("Control"))

        if self.check_abort():
            return


        
        ##############################################
        #
        # Perform the Stage-In definitions
        #
        ##############################################
        try:
            stagings = jsdl_doc.lookup_path("JobDefinition/JobDescription/"+
                                        "DataStaging")
        except KeyError, e:
            stagings = None

        img = self._mount_image()
        try:
            if self.check_abort():
                return
        
            # staging operations
            if stagings is not None:
                self._prepare_stagings(stagings,
                                       img.mount_point(),
                                       jsdl_doc.get_file_systems())

            if self.check_abort():
                return

            # setup scripts
            script_dir = os.path.join(self.spool, "scripts")
            if os.path.isdir(script_dir):
                self._call_scripts(
                    script_dir, "setup",
                    self.spool, img.mount_point() # passed to the script
                )
        finally:
            del img

        if self.check_abort():
            return

        # create swap space
        self._prepare_swap(jsdl_doc.lookup_path("JobDefinition/JobDescription/Resources"))
        
        log.info("preparation complete!")

    def undo(self):
        log.warn("undo not yet supported")

    def _prepare_swap(self, resources):
        from xbe.util.disk import makeSwap
        path = os.path.join(self.spool, "swap")
        makeSwap(path, 256)
        
    def _prepare_stagings(self, stagings, img_mount_point, known_filesystems):
        log.debug("performing the staging operations")
        for staging in stagings:
            if self.check_abort():
                return
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
        self._handle_location(package["Location"], dst_dir=self.spool)

    def _prepare_inst(self, inst):
        if self.ctxt.check_abort():
            return

        log.debug("preparing from inline instance description:")

        log.debug("getting kernel...")
        self._handle_location(inst["Kernel"]["Location"],
                              dst_dir=self.spool, dst_file="kernel")

        if self.ctxt.check_abort():
            return

        if inst.get("Initrd") is not None:
            log.debug("getting initrd...")
            self._handle_location(inst["Initrd"]["Location"],
                                  dst_dir=self.spool, dst_file="initrd")

        if self.ctxt.check_abort():
            return
        log.debug("getting image...")
        self._handle_location(inst["Image"]["Location"],
                              dst_dir=self.spool, dst_file="image")

    def _prepare_control_files(self, control):
        log.debug("preparing control files")
        script_dir = os.path.join(self.spool, "scripts")
        try:
            os.makedirs(script_dir)
        except OSError, e:
            if e.errno == errno.EEXIST:
                pass
            else:
                raise
        counters = {}
        for script in control["Script"]:
            if self.ctxt.check_abort():
                return
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

class TearDownActivity(TaskActivity):
    def __init__(self, spool):
        """performs tear down activities.
        * calling tear-down scripts
        * staging files out
        """
        TaskActivity.__init__(self, spool)
        self.register_location_handler(StageOutHandler(self))

    def perform(self, jsdl_doc):
        """prepare the given jsdl_doc.
        
        spool_path is the path to some directory where the files will
        be retrieved to.

        jsdl_doc is a parsed and validated JSDL document.

        returns a ComplexActivity.
        """
        if self.check_abort():
            return

        if not os.path.exists(os.path.join(self.spool, "image")):
            raise ValueError("could not find 'image' within the spool")

        ##############################################
        #
        # Perform the Stage-Out definitions
        #
        ##############################################
        try:
            stagings = jsdl_doc.lookup_path("JobDefinition/JobDescription/"+
                                        "DataStaging")
        except KeyError, e:
            stagings = None

        # try to get the working directory
        try:
            wd = jsdl_doc.lookup_path("JobDefinition/JobDescription/"+
                                      "Application/POSIXApplication/"+
                                      "WorkingDirectory")
        except Exception, e:
            wd = "/"

        img = self._mount_image()
        try:
            if self.check_abort():
                return
        
            # staging operations
            if stagings is not None:
                self._unprepare_stagings(stagings,
                                         img.mount_point(),
                                         wd, jsdl_doc.get_file_systems())

            if self.check_abort():
                return

            # cleanup scripts
            script_dir = os.path.join(self.spool, "scripts")
            if os.path.isdir(script_dir):
                self._call_scripts(
                    script_dir, "cleanup",
                    self.spool, img.mount_point() # passed to the script
                )
        finally:
            del img

        log.info("un-preparation complete!")

    def undo(self):
        pass

    def _unprepare_stagings(self, stagings, img_mount_point,
                            working_directory, known_filesystems):
        log.debug("performing the stage out operations")
        for staging in stagings:
            if staging.get("Target") is None:
                # stage-in operation
                log.debug("ignoring stagein-only operation")
                continue
            self._handle_location(staging,
                                  img_mount_point,
                                  working_directory, known_filesystems)

class AcquireResourceActivity(ActivityProxy):
    implements(IUndoable)
    
    def __init__(self, resource_pool, timeout=1):
        ActivityProxy.__init__(self)
        self.pool = resource_pool
        self.timeout = timeout
        self.resource = None

    def __call__(self, ctxt, *a, **kw):
        if self.resource is not None:
            return self.resource
        
        rv = None
        while not ctxt.check_abort():
            try:
                rv = self.pool.acquire(self.timeout)
            except Exception, e:
                pass
            else:
                # got some resource
                break

        self.lock()
        self.resource = rv
        self.unlock()
        return rv

    def undo(self):
        try:
            self.lock()
            r = self.resource
            self.resource = None
            self.pool.release(r)
        finally:
            self.unlock()

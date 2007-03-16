"""A module that describes several activities made by a task.

* retrieve necessary files
* unpack packages
* validate hash values
* stage-in files into an image
"""

import sys, signal, os, os.path, threading, subprocess, errno, stat, time
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

    def __str__(self):
        return "<%(cls)s with exitcode %(code)d>" % {
            "cls": self.__class__.__name__,
            "code":self.exitcode,
        }
    __repr__ = __str__

class ActivityFailed(Exception):
    def __str__(self):
        return "<%(cls)s - %(msg)s - %(args)s>" % {
            "cls": self.__class__.__name__,
            "msg": self.message,
            "args": pformat(self.args)
        }
    __repr__ = __str__

class StagingException(Exception):
    pass
class StagingAborted(StagingException):
    pass
class StageInFailed(StagingException):
    pass
class StageOutFailed(StagingException):
    pass

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
            log.debug("retrieved to %s", dst)
        except StagingAborted:
            return
        finally:
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
            log.debug("uploaded %s", src)
        except StagingAborted:
            return
        finally:
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
        log.debug("looking up cache-id %s", cache_id)

        import threading
        from twisted.python import failure
        from twisted.internet import defer

        cv = threading.Condition()
        def notify(result):
            cv.acquire()
            cv.notifyAll()
            self.__result = result
            cv.release()
        d = xbed.cache.lookupByUUID(cache_id)
        d.addBoth(notify)

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
        log.debug("retrieving: %r", uri)
        if dst_file is None:
            filename = uri.split("/")[-1]
        else:
            filename = dst_file
        dst = os.path.join(dst_dir, filename)

        self.perform_download(uri, dst)

        self.activity.check_abort()

        # verify the hash value
        hash_validator = location.get("Hash")
        if hash_validator is not None:
            log.debug("validating data")
            if not hash_validator.validate(open(dst, 'rb')):
                raise ValidationError("the retrieved file did not match the hash-value",
                                      uri, hash_validator.algorithm(),
                                      hash_validator.hexdigest()
                )

        self.activity.check_abort()

        # decompress the file if necessary
        compression = location.get("Compression")
        if compression is not None:
            log.debug("decompressing %s", dst)
            compression.decompress(file_name=dst, remove_original=True)

        # change the mode if desired
        mode = location.get("Mode")
        if mode is not None:
            os.chmod(dst, mode)

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
            
            log.debug("uploading: %s -> %s", file_name, uri)
            
            # make file relative to image mount_point
            real_file_name = os.path.join(mount_point, file_name.lstrip("/"))
            if not os.path.exists(real_file_name):
                raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), file_name)
            return self.perform_upload(real_file_name, uri)

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
            if self.ctxt.check_abort():
                raise StagingAborted()
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
                    log.info("error while terminating subprocess", exc_info=1)
                    raise
        finally:
            self.unlock()

    def __call__(self, context, jsdl_doc, logbook=[]):
        if not isinstance(jsdl_doc, jsdl.JsdlDocument):
            raise ValueError("jsdl_doc must be a JsdlDocument", jsdl_doc)
        if not os.path.exists(self.spool):
            raise ValueError("spool_path must exist", self.spool)

        self.ctxt = context
        self.logbook = logbook
        try:
            rv = self.perform(jsdl_doc)
        except StagingAborted:
            log.debug("staging has been aborted")
        except Exception, e:
            log.debug("staging operation failed", exc_info=1)
            raise e
        return rv

    def perform(self, jsdl_doc):
        raise NotImplementedError("implement 'perform' in a subclass")

    def undo(self):
        raise NotImplementedError("implement 'undo' in a subclass")

    def _call_scripts(self, script_dir, script_prefix, jail_path, *args):
        if not os.path.exists(script_dir):
            return
        for script in filter(lambda s: s.startswith(script_prefix),
                             os.listdir(script_dir)):
            self.check_abort()
            script_path = os.path.join(script_dir, script)
            script_path = self.make_path_relative_to(script_path, jail_path)
            log.debug("calling script '%s'", script_path)
            self._run_script(script_path, jail_path, *args)

    def _run_script(self, script, jail_path, *args):
        """Run the given script in the jail defined by jail_path and pass args to it."""
        try:
            self.lock()
            argv = ["/usr/sbin/chroot", jail_path, script]
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

    def _mount_image(self, image_path, directory):
        # mount the image
        from xbe.util import disk
        img = disk.mountImage(
            image_path,                          # path to the image file
            fs_type=disk.FS_EXT3,                # filesystem type
            dir=directory                        # where to mount the image
        )
        log.debug("mounted image to '%s'", img.mount_point())
        return img

    def make_path_relative_to(self, path, parent):
        return path.replace(parent.rstrip('/'), '', 1)

class SetUpActivity(TaskActivity):
    def __init__(self, spool, jail_package, jail_compression="tbz"):
        """prepares necessary files for a task.

        Spool is the spool directory of the given task.
            * such as /srv/xen-images/tasks/{task-id}/

        Whitin that spool the following takes place:
            1. retrieve the jail_package (a tarred directory hierarchie of a jail)
               this *must* create the {spool}/jail directory
            2. retrieve all files defined in the jsdl to {spool}/jail/var/xbe-spool
                  * instance-package or image,kernel,initrd
                  * control scripts (to {spool}/jail/var/xbe-spool/scripts
            3. call each setup script in a chroot environment
            4. create a swap-partition for the instance
        """
        TaskActivity.__init__(self, spool)

        from xbe.xml.jsdl import Decompressor
        self._jail_location = {
            "URI": "file://"+jail_package,
            "Compression": Decompressor(jail_compression),
        }
        del Decompressor
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

        self.check_abort()

        ##############################################
        #
        # setup the jail
        #
        ##############################################
        log.info("setting up the jail")
        try:
            self._handle_location(self._jail_location, self.spool)
        except Exception, e:
            log.debug("jail could not be retrieved: %s", e)
            raise e

        self.check_abort()

        self.jail_path = os.path.join(self.spool, "jail")
        if not os.path.exists(self.jail_path):
            raise StageInFailed("jail setup failed", self.jail_path)

        # the path where all files are staged to
        self.xbe_spool = os.path.join(self.jail_path, "var", "xbe-spool")
        if not os.path.exists(self.xbe_spool):
            try:
                os.makedirs(self.xbe_spool)
            except Exception, e:
                raise StageInFailed("jail setup failed, could not create spool directory", e)
        self.proc_path = os.path.join(self.jail_path, "proc")
        if not os.path.exists(self.proc_path):
            try:
                os.makedirs(self.proc_path)
            except Exception, e:
                raise StageInFailed("jail setup failed, could not create proc directory", e)
        log.info("jail has been set up")


        ##############################################
        #
        # Retrieve a package or an inline definition
        #
        ##############################################
        if instdesc.get("Package") is not None:
            self._prepare_package(instdesc.get("Package"))
        else:
            self._prepare_inst(instdesc.get("Instance"))

        self.check_abort()

        
        ##############################################
        #
        # get the control scripts
        #
        ##############################################
        if instdesc.get("Control") is not None:
            self._prepare_control_files(instdesc.get("Control"))

        self.check_abort()

        
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

        try:
            # mount the proc filesystem
            subprocess.check_call(["mount", "-t", "proc", "proc", self.proc_path])
            
            # call the pre-setup hooks, they may modify the image in place
            self._call_scripts(os.path.join(self.xbe_spool, "scripts"), "pre-setup", self.jail_path)
        
            img = self._mount_image(os.path.join(self.xbe_spool, "image"),
                                    self.xbe_spool)
            try:
                # staging operations
                if stagings is not None:
                    self._prepare_stagings(stagings,
                                           img.mount_point(),
                                           jsdl_doc.get_file_systems())

                    self.check_abort()

                # setup scripts
                self._call_scripts(os.path.join(self.xbe_spool, "scripts"), "setup", self.jail_path,
                                   self.make_path_relative_to(img.mount_point(),
                                                              self.jail_path) # passed to the script
                )
            finally:
                del img
        finally:
            # umount the proc filesystem
            subprocess.check_call(["umount", self.proc_path])

        self.check_abort()

        # create swap space
        self._prepare_swap(jsdl_doc.lookup_path("JobDefinition/JobDescription/Resources"))
        
        log.info("preparation complete!")

    def undo(self):
        log.warn("undo not yet supported")

    def _prepare_swap(self, resources):
        from xbe.util.disk import makeSwap
        path = os.path.join(self.xbe_spool, "swap")
        # TODO: find out some meaningful value for this one
        #       maybe TotalVirtualMemory
        tot_vmem = resources.get("TotalVirtualMemory")
        if tot_vmem is not None:
            vmem = int(tot_vmem.get_value())
        else:
            vmem = 256
        makeSwap(path, vmem)
        
    def _prepare_stagings(self, stagings, img_mount_point, known_filesystems):
        log.debug("performing the staging operations")
        for staging in stagings:
            self.check_abort()
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
        self._handle_location(package["Location"], dst_dir=self.xbe_spool)

    def _prepare_inst(self, inst):
        self.check_abort()

        log.debug("preparing from inline instance description:")

        log.debug("getting kernel...")
        self._handle_location(inst["Kernel"]["Location"],
                              dst_dir=self.xbe_spool, dst_file="kernel")

        self.check_abort()

        if inst.get("Initrd") is not None:
            log.debug("getting initrd...")
            self._handle_location(inst["Initrd"]["Location"],
                                  dst_dir=self.xbe_spool, dst_file="initrd")

        self.check_abort()
        
        log.debug("getting image...")
        self._handle_location(inst["Image"]["Location"],
                              dst_dir=self.xbe_spool, dst_file="image")

    def _prepare_control_files(self, control):
        log.debug("preparing control files")
        script_dir = os.path.join(self.xbe_spool, "scripts")
        try:
            os.makedirs(script_dir)
        except OSError, e:
            if e.errno == errno.EEXIST:
                pass
            else:
                raise
        counters = {}
        for script in control["Script"]:
            self.check_abort()
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
        self.check_abort()

        self.jail_path = os.path.join(self.spool, "jail")
        self.proc_path = os.path.join(self.jail_path, 'proc')
        self.xbe_spool = os.path.join(self.jail_path, "var", "xbe-spool")

        if not os.path.exists(os.path.join(self.xbe_spool, "image")):
            raise StageOutFailed("could not find 'image' within the spool", self.xbe_spool)

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


        try:
            # mount the proc filesystem
            subprocess.check_call(["mount", "-t", "proc", "proc", self.proc_path])

            img = self._mount_image(os.path.join(self.xbe_spool, "image"),
                                    self.xbe_spool)
            try:
                self._call_scripts(os.path.join(self.xbe_spool, "scripts"), "cleanup", self.jail_path,
                                   # passed to the script
                                   self.make_path_relative_to(img.mount_point(), self.jail_path)
                )

                # staging operations
                if stagings is not None:
                    self._unprepare_stagings(stagings,
                                             img.mount_point(),
                                             wd, jsdl_doc.get_file_systems())

                self.check_abort()
            finally:
                del img

            # call the post-cleanup hooks, they may for instance transfer the image to some place
            self._call_scripts(os.path.join(self.xbe_spool, "scripts"), "post-cleanup", self.jail_path)
        finally:
            # umount the proc filesystem
            subprocess.check_call(["umount", self.proc_path])
        
        log.info("un-preparation complete!")

    def undo(self):
        pass

    def _unprepare_stagings(self, stagings, img_mount_point,
                            working_directory, known_filesystems):
        log.debug("performing the stage out operations")
        for staging in stagings:
            if staging.get("Target") is None:
                continue
            self.check_abort()

            try:
                self._handle_location(staging,
                                      img_mount_point,
                                      working_directory, known_filesystems)
            except OSError, e:
                log.info("could not perform upload: %s", e)
                self.logbook.append("warning: upload failed: " + str(e))
            except Exception, e:
                log.info("could not perform upload: %s", e)
                self.logbook.append("warning: upload failed: " + str(e))
                
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

class InstanceStartFailed(ActivityFailed):
    pass
class InstanceStartTimedOut(InstanceStartFailed):
    pass
    
class StartInstanceActivity(ActivityProxy):
    def __init__(self, instance):
        ActivityProxy.__init__(self)
        self.instance = instance

    def __call__(self, ctxt, timeout, **kw):
        # 1. start the  instance
        try:
            self.instance.start()
        except Exception, e:
            raise InstanceStartFailed("backend instance could not be started", e)

        # 2. wait until it is really available
        timeout_time = time.time() + timeout
        while not ctxt.check_abort():
            if time.time() > timeout_time:
                log.debug("instance did not come up correctly within %d seconds", timeout)
                try:
                    log.debug("stopping the timed out instance")
                    self.instance.stop()
                except Exception, e:
                    log.warn("stopping of instance failed", exc_info=1)
                raise InstanceStartTimedOut("instance start timed out", self.instance)
            
            if self.instance.is_available():
                break
            elif self.instance.has_failed():
                raise InstanceStartFailed("instance start failed", self.instance)
            # wait a little bit
            try:
                time.sleep(2)
            except:
                pass
        if ctxt.check_abort():
            try:
                self.instance.stop()
            except Exception, e:
                log.warn("could not stop instance %s: %s", self.instance, e)

    def undo(self):
        try:
            self.lock()
            if self.instance.is_started():
                try:
                    self.instance.stop()
                except Exception,e:
                    log.warn("could not stop instance %s: %s", self.instance, e)
        finally:
            self.unlock()

class ExecutionFailed(ActivityFailed):
    pass

class ExecutionActivity(ActivityProxy):
    def __init__(self, task, wait_tuple):
        ActivityProxy.__init__(self)
        self.task = task
        self.wait_tuple = wait_tuple

    def __call__(self, ctxt, *args, **kw):
        if not ctxt.check_abort():
            self.task.sendJSDLToInstance()
        else:
            return
        
        rv = None
        while not ctxt.check_abort():
            self.wait_tuple[0].acquire()
            try:
                self.wait_tuple[0].wait()
                if self.wait_tuple[1] is not None:
                    rv = self.wait_tuple[1]
                    break
            finally:
                self.wait_tuple[0].release()

        if ctxt.check_abort():
            return

        # if the result is not an exitcode (int-type), raise an error
        if not isinstance(rv, int):
            raise ExecutionFailed("execution failed", rv)
        else:
            return rv

    def abort(self):
        self.wait_tuple[0].acquire()
        try:
            self.wait_tuple[0].notify()
        finally:
            self.wait_tuple[0].release()

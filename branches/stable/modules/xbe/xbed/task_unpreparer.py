"""A class that is able to do stage-out stuff for a task.

* pack files
* stage out necessary files
"""

import logging, os, os.path, sys, subprocess, errno, stat
log = logging.getLogger(__name__)

from zope.interface import Interface, implements
from lxml import etree
from pprint import pprint, pformat

from xbe.xml import jsdl
from xbe.util.staging import DataStager
from xbe.xbed.daemon import XBEDaemon
from xbe.xbed.task_preparer import ScriptFailed


class DataStagingHandler:
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
            return self.handle_upload(file_name, ds["Target"]["URI"], mount_point)

    def handle_upload(self, file_name, uri, mount_point):
        log.debug("uploading: %s -> %s" % (file_name, uri))

        # make file relative to image mount_point
        file_name = os.path.join(mount_point, file_name.lstrip("/"))

        stager = DataStager(file_name, uri)
        rv = stager.perform_upload()
        log.debug("uploaded to %s" % (uri))
        return rv

class UnPreparer(object):
    def __init__(self):
        """un-prepares a task."""
        self.__locationHandler = [
            DataStagingHandler() # the default handler
        ]

    def register_location_handler(self, handler, default=False):
        """Register a new location handler with this preparer."""
        if default:
            self.__locationHandler[0] = handler
        else:
            if handler not in self.__locationHandler:
                self.__locationHandler.append(handler)

    def unprepare(self, spool_path, jsdl_doc):
        """un-prepare the given jsdl_doc.
        
        spool_path is the path to some directory where the image can
        be found.

        jsdl_doc is a parsed and validated JSDL document.
        """
        if not isinstance(jsdl_doc, jsdl.JsdlDocument):
            raise ValueError("jsdl_doc must be a JsdlDocument", jsdl_doc)
        if not os.path.exists(spool_path):
            raise ValueError("spool_path must exist", spool_path)
        if not os.path.exists(os.path.join(spool_path, "image")):
            raise ValueError("could not find 'image' within the spool")

        self.__spool = spool_path

        # mapping from logical name to mount-point
        known_filesystems = jsdl_doc.get_file_systems()

        # now we can handle the stage out definitions
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
                self._unprepare_stagings(stagings,
                                         img.mount_point(),
                                         wd,
                                         known_filesystems)

            # cleanup scripts
            script_dir = os.path.join(self.__spool, "scripts")
            if os.path.isdir(script_dir):
                self._call_scripts(
                    script_dir, "cleanup",
                    self.__spool, img.mount_point() # passed to the script
                )
        finally:
            del img

        log.info("un-preparation complete!")

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

    def _handle_location(self, location, *args, **kw):
        for h in self.__locationHandler:
            if h.can_handle(location):
                return h.handle(location, *args, **kw)
        raise ValueError("I cannot handle this location-element", location)

"""
The XenBEE instance module (server side)

contains:
    InstanceManager:
	used to create new instances
	manages all currently available instances
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

import logging, os, os.path, time
import threading
log = logging.getLogger(__name__)

try:
    from traceback import format_exc as format_exception
except:
    from traceback import format_exception

from xbe.util.exceptions import *
from xbe.xbed.backend import backend
from xbe import util
from xbe.xml import xsdl

from twisted.internet import reactor, threads, task, defer
from twisted.python import failure
from urlparse import urlparse

class InstanceError(XenBeeException):
    pass

class InstanceTimedout(InstanceError):
    def __init__(self, msg, id):
        InstanceError.__init__(self, msg)
        self.id = id

class Instance(object):
    def __init__(self, xml_doc, config, spool, mgr):
        """Initialize a new instance.

        config -- an InstanceConfig object that holds all necessary
        information about the instance.

        Requirement:
	    config.name must be a UUID.

        """

        # check if the instance name is a UUID
        # example: 85a21198-89db-11db-a9dc-d3d26ec3b24a
        import re
        uuid_pattern = r"^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$"
        p = re.compile(uuid_pattern)
        if not p.match(config.getInstanceName()):
            raise InstanceError("instance name is not a UUID: %s" % config.getInstanceName())
        self.config = config
        self.xml_definition = xml_doc
        self.state = "created"
        
        # on instance-startup, a timer is created which results in notifying a failure
        # if the instance does not respond within __availableTimeout seconds
        self.__availableTimeout = 1*60
        self.__availableTimer = None # the deferred timer
        self.__availableDefer = defer.Deferred()

        self.spool = spool
        self.backend_id = -1
	self.mgr = mgr
        self.startTime = 0
        self.protocol = None # the protocol used to speak to the instance
        self.task = None

    def __del__(self):
        log.debug("deleting instance")

    def uuid(self):
        """Return the UUID for this instance.

        This uuid does not have anything in common with a possible
        backend-uuid.

        currently the same as self.config.getInstanceName()

        """
        return self.config.getInstanceName()

    def ID(self):
        return self.uuid()

    def getName(self):
        """Return the instance name.

        same as self.config.getInstanceName()

        """
        return self.config.getInstanceName()

    def getConfig(self):
        """Return the underlying config."""
        return self.config

    def getBackendID(self):
        return self.backend_id

    def setBackendID(self, b_id):
        self.backend_id = b_id

    def addFile(self, uri, logical_name, copy=True):
        """retrieves the uri and stores it as logical_name within the spool."""
        dst = os.path.join(self.getSpool(), logical_name)
        if os.access(dst, os.F_OK):
            log.error("a file with the logical name '%s' does already exist." % logical_name)
            raise InstanceError("logical file '%s' already exists." % logical)

        from xbe.util.staging import DataStager
        try:
            ds = DataStager(uri, dst)
            ds.perform(asynchronous=False)
        except Exception, e:
            log.error("could not put file from: %s into spool: %s" % (uri, str(e)))
            raise InstanceError("could not retrieve %s: %s" % (uri, str(e)))
        return dst


    def __parseFiles(self, elem):
        files = {}
        for f in elem.findall(xsdl.XSDL("File")):
            fid = f.attrib[xsdl.Tag("id")]
            uri = f.findtext(xsdl.XSDL("URI"))
            if uri == None:
                raise ValueError("no URI given for file: "+fid)
            files[fid] = { "URI": uri, "name": fid }
        return files

    def prepare(self):
        log.debug("starting preparation of instance %s" % (self.ID(),))

        inst_desc = self.xml_definition.find(xsdl.XSDL("InstanceDescription"))

        # put all File element into a dictionary
        #   id -> {URI, name}
        # the name defaults to the id and can be changed later
        files = self.__parseFiles(inst_desc.find(xsdl.XSDL("Files")))

        from pprint import pformat
	log.debug("files to retrieve:\n" + pformat(files))

        kernel_id = inst_desc.find(xsdl.XSDL("StartupParameters/Kernel")).attrib[xsdl.Tag("file-ref")]
        kernel_params = dict(
            [ (p.attrib[xsdl.Tag("param")], p.text)
              for p in inst_desc.findall(xsdl.XSDL("StartupParameters/KernelParameter")) ])
        initrd_id = inst_desc.find(xsdl.XSDL("StartupParameters/Initrd")).attrib[xsdl.Tag("file-ref")]
        images = [ img.attrib[xsdl.Tag("file-ref")] for img in inst_desc.findall(xsdl.XSDL("StartupParameters/Images/Image")) ]

        self.keep_running = inst_desc.find(xsdl.XSDL("RuntimeParameters/keep-running")) is not None

        ctr = 1
        for img in images:
            self.config.addDisk(self.getFullPath(img), "sda"+str(ctr))
            ctr += 1
        self.config.setKernel(self.getFullPath(kernel_id))
        self.config.setInitrd(self.getFullPath(initrd_id))

        self.config.addToKernelCommandLine(XBE_SERVER="%s:%d" % (
            "xen-o-matic.itwm.fhrg.fraunhofer.de", 61613))
        self.config.addToKernelCommandLine(XBE_UUID="%s" % (self.getName(),))
        for k,v in kernel_params.iteritems():
            if v is not None:
                self.config.addToKernelCommandLine("%s=%s" % (k,v))
            else:
                self.config.addToKernelCommandLine("%s" % (k))

        macs = [ "00:16:3e:00:00:01",
                 "00:16:3e:00:00:02" ]
        import random
        mac = random.choice(macs)
        log.debug("TODO: choose meaningful MAC: %s" % (mac))
        self.config.setMac(mac)
    
        return self.addFiles(
            dict([ (f["name"], f["URI"]) for f in files.values()] ))
        
    def addFiles(self, mapping={}, **kwords):
        """Add several files to this instance.

        The 'key' is the logical filename under which the files are stored.
        The 'values' are the files to retrieve.

        Example:
	    addFiles(kernel='file:///boot/vmlinuz',
		disk1='http://www.example.com/instance/test.img')

	    will copy the files '/boot/vmlinuz' (local) and '/instance/test.img'
	    (from www.example.com) to the spool directory as 'kernel' and 'disk1'.

        """
        mapping.update(kwords)

        tmpFileList = [(uri, self.getFullPath(name)) for name,uri in mapping.iteritems()]

        # check the URIs and replace those starting with "cache:" with their real URIs

        _defers = []
        def _got_uri(uri, path):
            return (uri, path)

        for uri, path in tmpFileList:
            o = urlparse(uri)
            if o.scheme == "cache":
                cache_uuid = o.path.split("/")[-1]
                log.debug("looking up cache-id %s" % cache_uuid)
                d = self.mgr.cache.lookupByUUID(cache_uuid).addCallback(_got_uri, path)
            else:
                # just add the uri as is
                d = defer.succeed(uri).addCallback(_got_uri, path)
            _defers.append(d)

        def _cache_finished(results):
            log.debug("cache lookup finished")
            fileList = []
            for result, uri_path_pair in results:
                if result == defer.FAILURE:
                    raise InstanceError("could not translate cache-uri: %s" % str(uri_path_pair))
                fileList.append(uri_path_pair)
            return fileList

        def _retrieve_files(fileList):
            log.debug("starting retriever")
            from xbe.util.staging import FileSetRetriever
            retriever = FileSetRetriever(fileList)
            return retriever.perform()
            
        dL = defer.DeferredList(_defers)

        def _log_failure(err):
            self.state = "failed"
            log.error("retrieval failed: "+err.getTraceback())
        for _d in _defers:
            _d.addErrback(_log_failure)
            
        dL.pause()
        dL.addCallback(_cache_finished)
        dL.addCallback(_retrieve_files)

        def __dl_callback(arg):
            log.info("successfully retrieved all files for: "+self.getName())
            self.state = "start-pending"
            return self
        dL.addCallback(__dl_callback)
        dL.unpause()
        return dL

    def getFullPath(self, logical_name):
        return os.path.join(self.getSpool(), logical_name)

    def getSpool(self):
        """Return the spool directory."""
        return self.spool

    def getBackendState(self):
        """Return the backend state of this instance.

        see: xbe.xbed.backend.status

        """
        return backend.getStatus(self)

    def getInfo(self):
        """Return all information known about the backend instance."""
        binfo = backend.getInfo(self)
        binfo.ips = getattr(self, 'ips', [])
        binfo.fqdn = getattr(self, 'fqdn', 'n/a')
        return binfo

    def stopped(self, result):
        self.state = "stopped"
        self.backend_id = -1
        self.mgr.removeInstance(self)
        return self

    def stop(self):
        """Stop the instance."""
        if self.state in ["started", "available"]:
            return threads.deferToThread(backend.shutdownInstance,
                                         self).addCallback(self.stopped)
        else:
            return defer.succeed(self)

    def cleanUp(self):
        """Removes all data belonging to this instance."""

        # check backend state
        backend_state = backend.getStatus(self)
        if backend_state in (backend.status.BE_INSTANCE_NOSTATE,
                             backend.status.BE_INSTANCE_SHUTOFF,
                             backend.status.BE_INSTANCE_CRASHED):
            util.removeDirCompletely(self.getSpool())

    def destroy(self):
        """Destroys the given instance.

        actions made:
	    * stop the instance
	    * removes the complete spool directory

        Warning: all data belonging to that instance are deleted, so be warned.

        essentially the same as:
	    stop()
	    cleanUp()

        """
        self.stop()
        self.cleanUp()

    def startable(self):
        return self.state == "start-pending"

    def start(self):
        """Starts a new backend instance.

        It returns a Deferred object, that is called back, when the
        instance has notified us, i.e. when the instance could be
        started correctly and is able to contact us.

        """
        self.state = "starting"

        def timeout(deferred):
            log.warn("instance %s timed out" % self.ID())
            deferred.errback(InstanceTimedout("instance timedout", self.ID()))

        def cancelTimer(arg, timer):
            # got signal from the backend instance
            self.state = "available"
            timer.cancel()
            return arg
            
        self.__availableTimer = reactor.callLater(self.__availableTimeout,
                                                  timeout,
                                                  self.__availableDefer)
        self.__availableDefer.addCallback(cancelTimer, self.__availableTimer)
        
        # use the backend to start
	def __started(backendId):
	    self.state = "started"
            self.setBackendID(backendId)
            self.startTime = time.time()
            return self
        def __failed(err):
            self.state = "failed"
            log.error("starting failed: " + err.getErrorMessage())
            self.__availableTimer.cancel()
            self.__availableDefer.errback(err)
            return self
        threads.deferToThread(backend.createInstance, self).addCallback(__started).addErrback(__failed)
            
        return self.__availableDefer

    def available(self, inst_avail_msg):
        """Callback called when the 'real' instance has notified us."""
        log.debug("%s is now available at %s [%s]" % (self.ID(),
                                                      inst_avail_msg.fqdn(),
                                                      ", ".join(inst_avail_msg.ips())))
        self.fqdn = inst_avail_msg.fqdn()
        self.ips = inst_avail_msg.ips()
        if not self.__availableDefer.called:
            self.__availableDefer.callback(self)

class InstanceManager:
    """The instance-manager.

    Through this class every known instance can be controlled:
	- send data (messages) to the manager on the instance
	- handle received data
	- create a new one

    """
    def __init__(self, cache):
        """Initialize the InstanceManager."""
        self.instances = {}
        self.cache = cache
        self.__iter__ = self.instances.itervalues

    def newInstance(self, xml_doc, spool):
        """Returns a new instance.

        This instance does not have any files assigned.

        """
        from xbe.xbed.config.xen import InstanceConfig
        from xbe.util.uuid import uuid
        icfg = InstanceConfig(uuid())

        try:
            inst = Instance(xml_doc, icfg, spool, self)
        except:
            log.error(format_exception())
            raise
	
        # remember the instance in our db
        self.instances[inst.uuid()] = inst
        return inst

    def removeInstance(self, inst):
        """Remove the instance 'inst' from the manager.

        It is assumed that the instance has been stopped/destroyed
        before.

        """
        inst.mgr = None
        self.instances.pop(inst.uuid())

    def lookupByID(self, ID):
        return self.lookupByUUID(ID)

    def lookupByUUID(self, uuid):
        """Return the instance for the given identifier.

        returns the instance object or None

        """
        return self.instances.get(uuid, None)

    def lookupByBackendID(self, backend_id):
        """Return the instance with the given backend id."""
        for inst in self.instances.values():
            if inst.getBackendID() == backend_id:
                return inst
        return None

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

"""Functions usefull to create and manage disk images.

   sparse disks, swap space, file-system images
   (u)mount images, build fstab entries.
   
"""

import subprocess, tempfile, os, errno, time, random, sys
import threading
from xbe.util.exceptions import ProcessError

try:
    devnull_p = os.devnull
except:
    devnull_p = "/dev/null"
try:
    devnull = open(devnull_p, 'rw')
except OSError, e:
    raise ImportError("sorry, but I need %s to operate." % (devnull), e)

# the only currently supported filesystems
FS_GUESS = ()
FS_EXT2 = "ext2"
FS_EXT3 = "ext3"

_module_lock = threading.RLock()

class NotMountedException(Exception):
    pass

class Image(object):
    """Represents a filesystem image."""
    def __init__(self, path, fs_type=FS_GUESS):
        """Initialize the image.

        @param path the path to the image-file
        @param fs_type the filesystem type to be used
        """
        self.__path = path
        if fs_type == FS_GUESS:
            fs_type = guess_fs_type(path)
        self.__fs_type = fs_type

    def __del__(self):
        """Automatically umount the image and delete the mount-point."""
        try:
            self.umount()
        except NotMountedException:
            pass

    def fs_type(self):
        """Return the fs_type of the image."""
        return self.__fs_type

    def is_mounted(self):
        """Is the image currently mounted?"""
        try:
            self.__mount_point
        except AttributeError:
            return False
        return True

    def mount_point(self):
        """Return the current mount-point of the image.

        raises NotMountedException if the image is not mounted.
        """
        if not self.is_mounted():
            raise NotMountedException()
        return self.__mount_point[0]

    def mount(self, mount_point=None, *args, **kw):
        """Mount the image to a temporary mount-point.

        All arguments and keywords are passed through to tempfile.mkdtemp.

        On success it returns the path to the mount-point. If any
        error occurs, the created temporary directory gets removed.
        """
        _module_lock.acquire()
        try:
            if mount_point is None:
                mount_point = [tempfile.mkdtemp(*args, **kw),
                               True]
            else:
                mount_point = [mount_point,
                               False]
            try:
                p = subprocess.Popen(getCommand("mount") + ["-o", "loop", "-t",
                                      self.__fs_type, self.__path, mount_point[0]],
                                     stdout=devnull, stderr=subprocess.PIPE)
                stdout, stderr = p.communicate()
                if p.returncode != 0:
                    raise ProcessError(p.returncode, "mount", stderr, stdout)
            except OSError, e:
                raise RuntimeError("'mount' could not be called", e)
            except:
                # if it was a temporary mount point, remove it
                if mount_point[1]:
                    os.rmdir(mount_point[0])
                raise
            self.__mount_point = mount_point
        finally:
            _module_lock.release()
        return self.__mount_point[0]

    def __umount(self, force=False):
        try:
             mount_point = self.__mount_point
        except AttributeError:
             raise NotMountedException()

        _module_lock.acquire()
        try:
             try:
                if force:
                    p = subprocess.Popen(getCommand("umount")+["-f", "-l", mount_point[0]],
                                         stdout=devnull, stderr=subprocess.PIPE)
                else:
                    p = subprocess.Popen(getCommand("umount")+[mount_point[0]],
                                         stdout=devnull, stderr=subprocess.PIPE)
                stdout, stderr = p.communicate()
                if p.returncode != 0:
                    raise ProcessError(p.returncode, "umount", stderr, stdout)
             except OSError, e:
                raise RuntimeError("'umount' could not be called", e)
             except:
                raise
             del self.__mount_point
             if mount_point[1]:
                 os.rmdir(mount_point[0])
        finally:
             _module_lock.release()

    def umount(self, retries=2):
        """U(n)mount the image.

        If the image is currently mounted, umount it and delete the
        temporary mount-point.

        raises NotMountedException if the image is not currently mounted.
        """

        # the following has been taken from twisted.internet.protocol.ReconnectingClientFactory
        maxDelay = 3600
        initialDelay = 1.0
        # Note: These highly sensitive factors have been precisely measured by
        # the National Institute of Science and Technology.  Take extreme care
        # in altering them, or you may damage your Internet!
        factor = 2.7182818284590451 # (math.e)
        # Phi = 1.6180339887498948 # (Phi is acceptable for use as a
        # factor if e is too large for your application.)
        jitter = 0.11962656492 # molar Planck constant times c, Jule meter/mole

        delay = initialDelay

        def retry(retries, delay):
            if retries < 0:
                return False, retries, delay
            retries -= 1
            delay = min(delay * factor, maxDelay)
            if jitter:
                delay = random.normalvariate(delay, delay * jitter)
            time.sleep(delay)
            return True, retries, delay
                                        
        while True:
            try:
                self.__umount()
                break
            except NotMountedException:
                break
            except Exception, e:
                print >>sys.stderr, "umount failed", e
                do, retries, delay = retry(retries, delay)
                if not do:
                   try:
                      print >>sys.stderr, "forcing umount"
                      self.__umount(force=True)
                   except:
                       raise

def getCommand(cmd):
    if os.geteuid() != 0:
        return ["sudo", cmd]
    else:
        return [cmd]

def guess_fs_type(path):
    """Try to guess the file system type using the 'file' command.

    raises ValueError if no guess could be made.
    return the fs_type
    """
    try:
        p = subprocess.Popen(["file",
                              "-b", # brief output
                              path],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise ProcessError(p.returncode, "file", stderr, stdout)
        else:
            # single line: example: Linux rev 1.0 ext3 filesystem data
            file_info = stdout
            if file_info.find("filesystem data") > -1:
              components = file_info.split()
              return file_info.split()[3]
            else:
                raise ValueError("could not guess filesystem type")
    except OSError, e:
        raise

def mountImage(path, fs_type=FS_GUESS, *args, **kw):
    """Mount an image using the loop device.

    returns a Image instance which is already mounted.

    @param path is the path to the image file
    @param fs_type the filesystem type to use, defaults to FS_GUESS,
           which means that an attempt is made to guess the correct
           fs_type
           
    all additional parameters will be passed to tempfile.mkdtemp
    """
    img = Image(path, fs_type)
    img.mount(*args, **kw)
    return img

def makeSparseDisk(path, mega_bytes=128):
    """Creates a sparse.

    path -- the path where to generate the file.
    mega_bytes -- as the name says, the number of mega bytes.

    requires: dd

    raises ProcessError if 'dd' failed
    raises OSError if 'dd' could not be executed
    raises ValueError if mega_bytes did not convert to 'int'
    returns the given path
    """
    try:
        mega_bytes = int(mega_bytes)
    except:
        raise

    try:
        p = subprocess.Popen(["dd",
                              "if=%s" % devnull_p, "of=%s" % path,
                              "bs=1024k", "count=0", "seek=%d" % mega_bytes],
                             stdout=devnull, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise ProcessError(p.returncode, "dd", stderr, stdout)
    except OSError, e:
        raise
    return path

def makeSwap(path, mega_bytes=128):
    """Create a swap disk.

    Uses the makeSparseDisk to create a sparse disk of size
    'mega_bytes' at path and running 'mkswap' on it.

    requires: mkswap

    raises ProcessError if mkswap returned non zero
    raises LookupError if mkswap could not be found
    returns the given if successful path
    """
    makeSparseDisk(path, mega_bytes)
    try:
        search_path = os.environ["PATH"].split(":")
    except KeyError:
        search_path = ["/sbin", "/usr/sbin", "/usr/local/sbin"]
    success = False
    for prefix in search_path:
        try:
            cmd = os.path.join(prefix, "mkswap")
            p = subprocess.Popen([cmd, path],
                                 stdout=devnull, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                raise ProcessError(p.returncode, cmd, stderr, stdout)
        except OSError:
            # try the next one
            continue
        success = True
        break
    if not success:
        raise LookupError("could not locate mkswap")
    return path

def makeImage(path, fs_type="ext2", mega_bytes=128):
    """Create a new disk image.

    raises LookupError if mkfs could not be found
    raises 
    
    @param path location of the new image
    @param fs_type the file-system type to create
    @param mega_bytes the size of the new image
    """
    makeSparseDisk(path, mega_bytes)
    try:
        search_path = os.environ["PATH"].split(":")
    except KeyError:
        search_path = ["/sbin", "/usr/sbin", "/usr/local/sbin"]
        
    success = False
    for prefix in search_path:
        try:
            cmd = os.path.join(prefix, "mkfs")
# from the mkfs manpage:
# -F Force mke2fs to create a filesystem, even if the specified device
#    is  not  a partition  on  a block  special  device,  or if  other
#    parameters do not make sense.  In order to force mke2fs to create
#    a filesystem  even if the filesystem  appears to be in  use or is
#    mounted  (a truly  dangerous thing  to do),  this option  must be
#    specified twice.
            p = subprocess.Popen([cmd, "-t", fs_type, "-F", path],
                                 stdout=devnull, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                raise ProcessError(p.returncode, cmd, stderr, stdout)
        except OSError, e:
            # try the next path
            continue
        success = True
        break
    if not success:
        raise LookupError("could not locate mkfs")
    return Image(path, fs_type)

class FSTabEntry:
    """Represents a single entry in the fstab.

    """

    def __init__(self, file_system, mount_point, type, options="defaults", dump_freq=0, pass_no=0):
        self.__file_system = file_system
        self.__mount_point = mount_point
        self.__type = type
        self.__opts = self._parse_opts(options)
        self.__dump_freq = int(dump_freq)
        self.__pass_no = int(pass_no)

    def get_opts(self):
        return self.__opts
    def get_opt_string(self):
        return self._unparse_opts(self.__opts)
    def get_file_system(self):
        return self.__file_system
    def get_mount_point(self):
        return self.__mount_point
    def get_type(self):
        return self.__type
    def get_dump_freq(self):
        return self.__dump_freq
    def get_pass_no(self):
        return self.__pass_no

    def _unparse_opts(self, options):
        opts = []
        for key, value in options.iteritems():
            if value == 0: # and key in 'self.__boolOpts'
                key_value = "no"+key
            elif value == 1:
                key_value = key
            else:
                key_value = "%s=%s" % (key, value)
            opts.append(key_value)
        return ",".join(opts)

    def _parse_opts(self, optstring):
        options = {}
        opts = optstring.split(",")
        for opt in opts:
            key_value = opt.split("=", 1)
            if len(key_value) == 2:
                options[key_value[0]] = key_value[1]
            elif len(key_value) == 1:
                # have a look at the option and store 0 or 1 if it starts with 'no'
                val = 1
                key = key_value[0]
                if key.startswith("no"):
                    val = 0
                    key = key[2:]
                options[key] = val
        return options

    def __repr__(self):
        return "<%(cls)s %(fs)s on %(mp)s (%(type)s with %(opts)s)>" % {
            "cls": self.__class__.__name__,
            "fs" : self.__file_system,
            "mp" : self.__mount_point,
            "type":self.__type,
            "opts":self.get_opt_string() }
    def __str__(self):
        return "\t".join(map(str, (self.get_file_system(),
                                   self.get_mount_point(),
                                   self.get_type(),
                                   self.get_opt_string(),
                                   self.get_dump_freq(),
                                   self.get_pass_no())))

class FSTab:
    """Represents the /etc/fstab
    #
    # /etc/fstab: static file system information.
    #
    # <file system> <mount point>   <type>  <options>       <dump>  <pass>
    """
    def __init__(self):
        self.__entries = []
        self.__iter__ = self.__entries.__iter__
        self.__getitem__ = self.__entries.__getitem__
        self.__getslice__ = self.__entries.__getslice__

    def add(self, *args, **kw):
        self.__entries.append(FSTabEntry(*args, **kw))

    def __repr__(self):
        from pprint import pformat
        return pformat(self.__entries)

    def __str__(self):
        return self.to_fstab()

    def to_fstab(self):
        return "\n".join(map(str, self))

    def from_file(cls, f):
        fstab = cls()
        if not isinstance(f, file):
            f = open(f)
        for line in f.readlines():
            entry = line.strip().split("#", 1)[0]
            if entry == "":
                continue
            fstab.add(*entry.split())
        return fstab
    from_file = classmethod(from_file)

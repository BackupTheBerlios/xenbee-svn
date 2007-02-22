"""Functions usefull to create and manage disk images.

   sparse disks, swap space, file-system images
   (u)mount images
"""

import subprocess, tempfile, os

try:
    devnull_p = os.devnull
except:
    devnull_p = "/dev/null"
try:
    devnull = open(devnull_p, 'rw')
except OSError, e:
    raise ImportError("sorry, but I need %s to operate." % (devnull), e)

class ProcessError(subprocess.CalledProcessError):
    def __init__(self, returncode, cmd, stderr, stdout):
        subprocess.CalledProcessError.__init__(self, returncode, cmd)
        self.__stderr = stderr
        self.__stdout = stdout

    def __str__(self):
        s = subprocess.CalledProcessError.__str__(self)
        s += ": %s" % (self.__stderr)
        return s

# the only currently supported filesystems
FS_EXT2 = "ext2"
FS_EXT3 = "ext3"

class NotMountedException(Exception):
    pass

class Image(object):
    """Represents a filesystem image."""
    def __init__(self, path, fs_type=FS_EXT2):
        """Initialize the image.

        @param path the path to the image-file
        @param fs_type the filesystem type to be used
        """
        self.__path = path
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
        return self.__mount_point

    def mount(self, *args, **kw):
        """Mount the image to a temporary mount-point.

        All arguments and keywords are passed through to tempfile.mkdtemp.

        On success it returns the path to the mount-point. If any
        error occurs, the created temporary directory gets removed.
        """
        mount_point = tempfile.mkdtemp(*args, **kw)
        try:
            p = subprocess.Popen(["mount", "-o", "loop", "-t",
                                   self.__fs_type, self.__path, mount_point],
                                 stdout=devnull, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                raise ProcessError(p.returncode, "mount", stderr, stdout)
        except OSError, e:
            raise RuntimeError("'mount' could not be called", e)
        except:
            os.rmdir(mount_point)
            raise
        self.__mount_point = mount_point
        return self.__mount_point

    def umount(self):
        """U(n)mount the image.

        If the image is currently mounted, umount it and delete the
        temporary mount-point.

        raises NotMountedException if the image is not currently mounted.
        """
        try:
            mount_point = self.__mount_point
            del self.__mount_point
        except AttributeError:
            raise NotMountedException()
        try:
            p = subprocess.Popen(["umount", mount_point],
                                 stdout=devnull, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                raise ProcessError(p.returncode, "umount", stderr, stdout)
        except OSError, e:
            raise RuntimeError("'umount' could not be called", e)
        except subprocess.CalledProcessError, e:
            raise RuntimeError("'umount' failed", e)
        except:
            raise
        os.rmdir(mount_point)

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
            file_info = stdout.split()
            if len(file_info) == 6 and " ".join(file_info[-2:]) == "filesystem data":
                return file_info[-3]
            else:
                raise ValueError("could not guess filesystem type")
    except OSError, e:
        raise

def mountImage(path, fs_type=FS_EXT2, *args, **kw):
    """Mount an image using the loop device.

    returns a Image instance which is already mounted.

    @param path is the path to the image file
    @param fs_type the filesystem type to use (defaults to ext2)
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

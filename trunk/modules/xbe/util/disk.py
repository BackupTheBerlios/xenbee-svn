"""Functions usefull to create disk images.

   sparse disks, swap space

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

def makeSparseDisk(path, mega_bytes=128):
    """Creates a sparse.

    path -- the path where to generate the file.
    mega_bytes -- as the name says, the number of mega bytes.

    requires: dd
    
    """
    try:
        mega_bytes = int(mega_bytes)
    except:
        raise
    try:
        subprocess.check_call(["dd",
                               "if=%s" % devnull_p, "of=%s" % path,
                               "bs=1024k", "count=0", "seek=%d" % mega_bytes],
                              stdout=devnull, stderr=devnull)
    except subprocess.CalledProcessError, e:
        raise RuntimeError("dd returned non zero exit code", e)
    except OSError, e:
        raise

def makeSwap(path, mega_bytes=128):
    """Create a swap disk.

    Uses the makeSparseDisk to create a sparse disk of size
    'mega_bytes' at path and running 'mkswap' on it.

    requires: mkswap

    """
    makeSparseDisk(path, mega_bytes)
    try:
        search_path = os.environ["PATH"].split(":")
    except KeyError:
        search_path = ["/sbin", "/usr/sbin", "/usr/local/sbin"]
    for prefix in search_path:
        try:
            cmd = os.path.join(prefix, "mkswap")
            subprocess.check_call([cmd, path], stdout=devnull, stderr=devnull)
        except OSError:
            # try the next one
            continue
        except subprocess.CalledProcessError, e:
            raise RuntimeError("mkswap had non zero exitcode", e)
        break

def makeImage(path, fs_type="ext2", mega_bytes=128):
    """Create a new disk image.

    @param path location of the new image
    @param fs_type the file-system type to create
    @param mega_bytes the size of the new image
    """
    makeSparseDisk(path, mega_bytes)
    try:
        search_path = os.environ["PATH"].split(":")
    except KeyError:
        search_path = ["/sbin", "/usr/sbin", "/usr/local/sbin"]
    for prefix in search_path:
        try:
            cmd = os.path.join(prefix, "mkfs.%s" % fs_type)
# from the mkfs manpage:
# -F Force mke2fs to create a filesystem, even if the specified device
#    is  not  a partition  on  a block  special  device,  or if  other
#    parameters do not make sense.  In order to force mke2fs to create
#    a filesystem  even if the filesystem  appears to be in  use or is
#    mounted  (a truly  dangerous thing  to do),  this option  must be
#    specified twice.
            subprocess.check_call([cmd, "-F",  path]) #, stdout=devnull, stderr=devnull)
        except OSError:
            # try the next one
            continue
        except subprocess.CalledProcessError, e:
            raise RuntimeError("%s had non zero exitcode" % cmd, e)
        break

class NotMountedException(Exception):
    pass

FS_EXT2 = "ext2"
FS_EXT3 = "ext3"
FS_REISER="reiserfs"

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

    def mounted(self):
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
        if not self.mounted():
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
            subprocess.check_call(["mount", "-o", "loop", "-t", self.__fs_type, self.__path, mount_point])
        except OSError, e:
            raise RuntimeError("'mount' could not be called", e)
        except subprocess.CalledProcessError, e:
            raise RuntimeError("'mount' failed", e)
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
            subprocess.check_call(["umount", mount_point])
        except OSError, e:
            raise RuntimeError("'umount' could not be called", e)
        except subprocess.CalledProcessError, e:
            raise RuntimeError("'umount' failed", e)
        except:
            raise
        os.rmdir(mount_point)

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

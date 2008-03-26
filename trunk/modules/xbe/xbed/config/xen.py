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

"""
Some classes needed to configure a xen instance using libvirt.

$Date: 2006-12-12 03:19:08 +0100 (Tue, 12 Dec 2006) $
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

import time

class ConfigurationError(Exception):
    pass

class InstanceConfig:
    """Parameters required by a xen instance.

    kernel - which kernel to use
    initrd - an optional initrd image

    disk-images - the first will be the root disk

    vcpus - the number of virtual cpus
    memory - the memory to reserve
    MAC  --- the mac address
    
    """
    def __init__(self, name):
        """Initialize a new configuration using the given name."""
        
        self.name = name
        self.diskImages = []
        self.mac = None
        self.ip = ""
        self.netmask = ""
        self.gateway = ""
        self.memory = 128 * 1024**2
        self.kernel = None
        self.initrd = None
        self.cmdline = []
        self.vcpus = 1

    def getInstanceName(self):
        """Returns the instance name."""
        return self.name

    def validate(self):
        """Checks whether this configuration is valid or not.

        Does not check if used files exist, but whether all required parameters are specified.

        required: kernel
        """
        if self.vcpus < 1:
            raise ConfigurationError("InstanceConfig: vcpus < 1: %d" % self.vcpus)
        if not self.kernel:
            raise ConfigurationError("InstanceConfig: kernel is None")
        if not len(self.getDisks()):
            raise ConfigurationError("InstanceConfig: no disks")
        if not self.name or not len(self.name):
            raise ConfigurationError("InstanceConfig: illegal name")

    def setKernel(self, kernel):
        """Sets the kernel to be used."""
        self.kernel = kernel
    def getKernel(self):
        """Returns the used kernel."""
        return self.kernel

    def addToKernelCommandLine(self, *args, **kw):
        """Sets the kernel commandline that shall be passed."""
        for opt in args:
            self.cmdline.append(opt)
        for k,v in kw.iteritems():
            self.cmdline.append("%s=%s" % (k,v))
        
    def getKernelCommandLine(self):
        """Returns the kernel commandline."""
        return " ".join(self.cmdline)

    def setNumCpus(self, vcpus):
        """Sets the number of virtual cpus to be used."""
        self.vcpus = vcpus
    def getNumCpus(self):
        """Returns the number of virtual cpus."""
        return self.vcpus

    def setInitrd(self, initrd):
        """Sets the initial ramdisk to be used."""
        self.initrd = initrd
    def getInitrd(self):
        """Returns the initial ramdisk or None."""
        return self.initrd

    def addDisk(self, path, target):
        """Adds disk image.
        
        path - the path to the image file
        target - the device name that should be used in the instance
            for example: sda1, sda2...
            without the /dev prefix
        """
        self.diskImages.append( {"path" : path, "target": target} )
    def getDisks(self):
        return self.diskImages

    def setMac(self, mac):
        self.mac = mac
    def getMac(self):
        return self.mac

    def setIP(self, ip):
        self.ip = ip
    def getIP(self):
        return self.ip

    def setNetmask(self, nm):
        self.netmask = nm 
    def getNetmask(self):
        return self.netmask

    def setGateway(self, gw):
        self.gateway = gw
    def getGateway(self):
        return self.gateway

    def setMemory(self, mem):
        """Sets the memory to be used.

        Trailing modifier characters may be used, such as K, M or G to
        specify kilo-, mega- or giga bytes.

        Examples:
             128M == 128 * 1024**2 bytes
        """
        try:
            mem = str(mem).strip().lower()
        except Exception, e:
            cfgerr = ConfigurationError("invalid mem: %s" % str(mem))
            cfgerr.exception = e
        import re
        mem_pattern = r"^(?P<bytes>\d+)(?P<modifier>[gmkb]?)$"
        p = re.compile(mem_pattern)
        m = p.match(mem)
        if not m: raise ConfigurationError("invalid mem: %s" % mem)

                                     # interpret trailing characters
        modTable = { "b" : 1024**0,  # b - Just bytes
                     "k" : 1024**1,  # k - Kilo bytes
                     "m" : 1024**2,  # m - Mega bytes
                     "g" : 1024**3 } # g - Giga bytes
        self.memory = int(m.group("bytes")) * modTable.get(m.group("modifier"), 1)
        if (self.memory <= 0): raise ConfigurationError("invalid mem: %d" % self.memory)
        
    def getMemory(self, unit="b"):
        """Returns the amount of memory in bytes (default).

        The optional parameter unit can be used to retrieve the memory
        in a different scale than the default bytes. Examples are: b,
        k, m or g.
        """
        modTable = { "b" : 1024**0,
                     "k" : 1024**1,
                     "m" : 1024**2,
                     "g" : 1024**3 }
        if not unit in modTable.keys():
            raise ConfigurationError("no such modifier: %s" % unit)
        return int(self.memory / modTable.get(unit))

class XenConfigGenerator:
    """Generates Xen (text) configuration files."""

    def __call__(self, config):
        return self.generate(config)
    
    def generate(self, config):
        config.validate()
        self.config = config
        
        from StringIO import StringIO
        self.out = StringIO()

        self.write_heading()
        self.write_kernel()
        self.write_other()
        self.write_disks()
        self.write_networking()
        self.write_behavior()

        return self.out.getvalue()

    def _write_helper(self, k, v):
        if v:
            print >>self.out, k, "=", "%s" % repr(v)

    def write_heading(self):
        print >>self.out, "# Configuration for the xen-instance: %s" % self.config.getInstanceName()
        print >>self.out, "# created on: %s" % time.asctime()
        print >>self.out
        self._write_helper("name", self.config.getInstanceName())

    def write_kernel(self):
        print >>self.out, "# Kernel configuration"
        self._write_helper("kernel", self.config.getKernel())
        self._write_helper("ramdisk", self.config.getInitrd())
        # additional arguments to kernel
        if self.config.getKernelCommandLine():
            self._write_helper("extra", self.config.getKernelCommandLine())
        print >>self.out

    def write_other(self):
        print >>self.out, "# Memory and cpu configurtion"
        self._write_helper("memory", str(self.config.getMemory("m")))
        self._write_helper("vcpus", str(self.config.getNumCpus()))
        print >>self.out

    def write_disks(self):
        print >>self.out, "# Disk device(s)"
        
        # root
        self._write_helper("root", "/dev/"+self.config.getDisks()[0]["target"]+" ro")

        # all disks
        disks = []
        for disk in self.config.getDisks():
            disks.append( "tap:aio:%(path)s,%(target)s,w" % disk )
        self._write_helper("disk", disks)

    def write_networking(self):
        print >>self.out, "# Networking configuration"
        if self.config.getMac():
            vif = [ "mac=%s, bridge=xenbr0" % self.config.getMac() ]
        else:
            vif = [ 'bridge=xenbr0' ]
        self._write_helper("vif", vif)
        if self.ip != None:
           self._write_helper("ip", self.ip)
           self._write_helper("gateway", self.gateway)
           self._write_helper("netmask", self.netmask)
           self._write_helper("dhcp", "off")
        else:
           # use dhcp
           self._write_helper("dhcp", "dhcp")

    def write_behavior(self):
        print >>self.out, "# Behavior"
        self._write_helper("on_poweroff", "destroy")
        self._write_helper("on_reboot", "restart")
        self._write_helper("on_crash", "restart")
    
#from xml.dom.DOMImplementation import implementation
#import xml.utils

class LibVirtXMLConfigGenerator:
    """Generates xml configs for libvirt.

    A sample could look like this: (source: http://libvirt.org/format.html)

    <domain type='xen' id='18'>
        <name>fc4</name>
        <os>
            <type>linux</type>
            <kernel>/boot/vmlinuz-2.6.15-1.43_FC5guest</kernel>
            <initrd>/boot/initrd-2.6.15-1.43_FC5guest.img</initrd>
            <root>/dev/sda1</root>
            <cmdline> ro selinux=0 3</cmdline>
        </os>
        <memory>131072</memory>
        <vcpu>1</vcpu>
        <devices>
            <disk type='file'>
                <source file='/u/fc4.img'/>
                <target dev='sda1'/>
            </disk>
            <interface type='bridge'>
                <source bridge='xenbr0'/>
                <mac address='aa:00:00:00:00:11'/>
                <script path='/etc/xen/scripts/vif-bridge'/>
            </interface>
            <console tty='/dev/pts/5'/>
        </devices>
        <on_reboot>restart</on_reboot>
        <on_poweroff>destroy</on_poweroff>
        <on_crash>rename-restart</on_crash>
    </domain>
    """

    def generate(self, config, pretty=False):
        tree = self.generateXMLTree(config)
        # return xml-string
        if pretty:
            from xml.dom.ext import PrettyPrint as Print
        else:
            from xml.dom.ext import Print as Print
        import StringIO
        out = StringIO.StringIO()
        Print(tree, out)
        return out.getvalue()
        
    def generateXMLTree(self, config):
        config.validate()
        self.config = config
        self.start()

        self.build_os()
        self.build_other()
        self.build_devices()
        self.build_behavior()

        self.end()
        return self.document

    def __call__(self, cfg):
        return self.generate(cfg)

    def _createTextNode(self, tag, txt):
        node = self.document.createElement(tag)
        self._addText(node, txt)
        return node

    def _addText(self, node, txt):
        txt_n = self.document.createTextNode(txt)
        node.appendChild(txt_n)

    def start(self):
        self.document = implementation.createDocument(None,None,None)
        self.domain = self.document.createElement("domain")

        self.domain.setAttribute("type", "xen")
        name = self._createTextNode("name", self.config.getInstanceName())
        self.domain.appendChild(name)

        self.document.appendChild(self.domain)

    def build_os(self):
        doc = self.document
        os = doc.createElement("os")
        os.appendChild(self._createTextNode("type", "linux"))
        os.appendChild(self._createTextNode("kernel", self.config.getKernel()))
        if self.config.getInitrd():
            os.appendChild(self._createTextNode("initrd", self.config.getInitrd()))
        os.appendChild(self._createTextNode("root", "/dev/" + self.config.getDisks()[0]["target"]))
        # additional commandline
        if self.config.getKernelCommandLine():
            os.appendChild(self._createTextNode("cmdline", self.config.getKernelCommandLine()))

        self.domain.appendChild(os)

    def build_other(self):
        self.domain.appendChild(self._createTextNode("memory",
                                                     str(self.config.getMemory("k"))))
        self.domain.appendChild(self._createTextNode("vcpu",
                                                     str(self.config.getNumCpus())))

    def build_devices(self):
        doc = self.document
        devices = doc.createElement("devices")

        # disks
        for disk in self.config.getDisks():
            disk_n = doc.createElement("disk")
            disk_n.setAttribute("type", "file")

            source_n = doc.createElement("source")
            source_n.setAttribute("file", disk["path"])
            target_n = doc.createElement("target")
            target_n.setAttribute("dev", disk["target"])

            disk_n.appendChild(source_n)
            disk_n.appendChild(target_n)
            devices.appendChild(disk_n)

        # network
        if self.config.getMac():
            interface_n = doc.createElement("interface")
            interface_n.setAttribute("type", "bridge")
            
            source_n = doc.createElement("source")
            source_n.setAttribute("bridge", "xenbr0")
            mac_n = doc.createElement("mac")
            mac_n.setAttribute("address", self.config.getMac())
            script_n = doc.createElement("script")
            script_n.setAttribute("path", "vif-bridge")
                            
            interface_n.appendChild(source_n)
            interface_n.appendChild(mac_n)
            interface_n.appendChild(script_n)
            devices.appendChild(interface_n)
        
        self.domain.appendChild(devices)

    def build_behavior(self):
        self.domain.appendChild(self._createTextNode("on_reboot", "restart"))
        self.domain.appendChild(self._createTextNode("on_poweroff", "destroy"))
        self.domain.appendChild(self._createTextNode("on_crash", "rename-restart"))

    def end(self):
        pass

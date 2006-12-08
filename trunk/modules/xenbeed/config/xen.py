"""
Some classes needed for the interaction with xen.
"""

import time

class InstanceConfig:
	def __init__(self, name):
		self.instanceName = name

class XenConfigGenerator:
	def __init__(self):
		pass

	def generate(self, config):
		self.config = config
		self.config.date = time.asctime()

		s = """# Configuration for the Xen instance %(instanceName)s, created on
# %(date)s
"""
		s += self._generateKernelParameters()
		s += self._generateDiskParameters()
		s += self._generateHostname()
		s += self._generateNetworking()
		return s % self.config.__dict__
	def __call__(self, cfg):
		return self.generate(cfg)

	def _generateKernelParameters(self):
		return """# kernel configuration + memory
kernel = '/srv/xen-images/domains/xenhobel-1/kernel'
ramdisk = '/srv/xen-images/domains/xenhobel-1/kernel'
memory = '128'
"""

	def _generateDiskParameters(self):
		return """# disk devices
root = '/dev/sda1 ro'
disk = [ 'file:/srv/xen-images/domains/xenhobel-1/disk.img,sda1,w',
         'file:/srv/xen-images/domains/xenhobel-1/swap.img,sda2,w' ]
"""

	def _generateHostname(self):
		return """# hostname
name = '%(instanceName)s'
"""

	def _generateNetworking(self):
		return """# networking
vif = [ 'ip=10.199.136.101 bridge=xenbr1' ]
"""

	def _generateBehaviour(self):
		return """# behaviour
on_poweroff = 'destroy'
on_reboot = 'restart'
on_crash = 'restart'
"""


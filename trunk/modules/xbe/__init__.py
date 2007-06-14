# XenBEE is a software that provides remote execution of applications
# in self-contained virtual disk images via Xen.
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
	The Xen-based Execution environment module.
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging, logging.handlers, sys, os.path

def initLogging(logfile='/tmp/xbe.log'):
    if sys.hexversion >= 0x2040200:
	# threadName available
	thread = ":%(threadName)s"
    else:
	thread = ""

    # fix the 'currentframe' function in the logging module,
    # so that correct line numbers get logged:
    # see: http://sourceforge.net/tracker/index.php?func=detail&aid=1652788&group_id=5470&atid=105470
    logging.currentframe = lambda: sys._getframe(3)

    _fileHdlr = logging.FileHandler(logfile, 'w+b')
    _fileHdlr.setLevel(logging.DEBUG)
    _fileHdlr.setFormatter(logging.Formatter(
        '%(asctime)s [%(process)d]' + thread + ' %(name)s:%(lineno)d %(levelname)-8s %(message)s'))
    logging.getLogger().addHandler(_fileHdlr)

    _syslogHdlr = logging.handlers.SysLogHandler()
    _syslogHdlr.setLevel(logging.FATAL)
    _syslogHdlr.setFormatter(logging.Formatter(
        '[%(process)d]' + thread + ' %(name)-12s:%(lineno)d %(levelname)-8s %(message)s'))
    logging.getLogger().addHandler(_syslogHdlr)

    _stderrHdlr = logging.StreamHandler(sys.stderr)
    _stderrHdlr.setLevel(logging.WARN)
    _stderrHdlr.setFormatter(logging.Formatter(
        '[%(process)d]' + thread + ' %(name)-12s: %(levelname)-8s %(message)s'))
    logging.getLogger().addHandler(_stderrHdlr)

    # activate overall logging of messages with DEBUG-level
    logging.getLogger().setLevel(logging.DEBUG)

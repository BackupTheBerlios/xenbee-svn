#!/usr/bin/python

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

"""Start a HTTP-server and server files from a given directory."""

import sys, os
from optparse import OptionParser
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler as RequestHandler

def run():
    p = OptionParser()
    p.add_option("-P", "--port", dest="port", type="int", default=8888, help="listen on this port")
    p.add_option("-d", "--dir", dest="directory", type="string", default=os.getcwd(), help="server this directory")
    opts, args = p.parse_args()

    os.chdir(opts.directory)
    print "serving directory '%s' on port %d" % (opts.directory, opts.port)
    httpd = HTTPServer(('', opts.port), RequestHandler)
    httpd.serve_forever()

if __name__ == "__main__":
    run()

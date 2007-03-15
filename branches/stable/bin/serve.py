#!/usr/bin/python

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

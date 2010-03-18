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

"""This module provides some network related utility functions."""

import socket
import urlparse as py_urlparse

def discover_ips(peer):
    """discover the external ip(s) for this node.

    The process works as follows:
         for each address family (IPv6, IPv4) in that order:
             * bind to all interfaces using an arbitrary port
             * connect to peer
             * read back the socket name (i.e. the IP)

         since we were able to connect to the STOMP server somehow, we
         can simply connect to it a second time ;-) but this time we
         use the tcp connection just for discovering our own external
         ips.

    @param peer - the (host,port) tuple usable to connect to to some server.
    @return a list of IPs
    """
    ips = []
    for family, desc in [ (socket.AF_INET6, "IPv6"),
                          (socket.AF_INET, "IPv4")]:
        s = socket.socket(family, socket.SOCK_STREAM)
        s.bind(('', 0)) # bind to all interfaces, arbitrary port

        # now connect the socket to our STOMP server
        try:
            s.connect(peer)
        except (socket.gaierror, socket.error), e:
            continue
                
        # connect was successful, now get the needed information from the socket
        sock_nam = s.getsockname()
        ips.append(sock_nam[0])

        s.close()
        del s
    return ips

def urlparse(uri):
    if "stomp" not in py_urlparse.uses_netloc:
        py_urlparse.uses_netloc.append("stomp")
    return py_urlparse.urlparse(uri)


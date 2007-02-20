"""This module provides some network related utility functions."""

import socket

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

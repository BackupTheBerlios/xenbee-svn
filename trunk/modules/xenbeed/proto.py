#!/usr/bin/env python
"""
The Xen Based Execution Environment protocol
"""

__version__ = "$Rev$"
__author__ = "$Author: petry $"

import logging
log = logging.getLogger(__name__)

from stomp.proto import StompClient, StompClientFactory

# Twisted imports
from twisted.internet import reactor
from twisted.internet import reactor

import os, os.path

class XenBEEProtocol(StompClient):
    """Processing input received by the STOMP server."""

	def connectedReceived(self, frame):
	    # i am connected to the stomp server
	    log.debug("successfully connected to STOMP server, avaiting your commands.")
	    self.subscribe(self.factory.queue, auto_ack=True)

	def messageReceived(self, msg):
	    log.debug("got message\n%s" % msg.body)
	    try:
		client = msg.header["client-id"]
		self.send(queue="/queue/xenbee/clients/%s" % client, msg="huhu")
	    except KeyError:
		log.error("illegal message received")

	def errorOccured(self, msg, detail):
	    log.error("error-message: '%s', details: '%s'" % (msg, detail))

class XenBEEProtocolFactory(StompClientFactory):
    protocol = XenBEEProtocol

    def __init__(self, queue="/queue/xenbee/daemon"):
	StompClientFactory.__init__(self, user='daemon', password='none')
	self.queue = queue

    def clientConnectionFailed(self, connector, reason):
	log.error("connection to STOMP server failed!: %s" % reason)
	reactor.stop()

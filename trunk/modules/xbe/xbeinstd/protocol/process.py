import logging
log = logging.getLogger(__name__)

from twisted.internet.protocol import ProcessProtocol

class XBEProcessProtocol(ProcessProtocol):
    """The protocol used to handle process execution."""
    
    def __init__(self, handler):
        self.handler = handler

    def processEnded(self, status_object):
        log.debug("process ended: %s" % str(status_object))
        self.handler.processEnded(status_object)

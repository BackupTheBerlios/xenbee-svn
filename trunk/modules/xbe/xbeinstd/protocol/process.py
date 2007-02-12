import logging
log = logging.getLogger(__name__)

from twisted.internet.protocol import ProcessProtocol

class XBEProcessProtocol(ProcessProtocol):
    """The protocol used to handle process execution."""
    
    def __init__(self, handler):
        self.errOutput = []
        self.stdOutput = []
        self.handler = handler
    
    def connectionMade(self):
        pass

    def outReceived(self, data):
        """parse the data and store it in some file."""
        self.stdOutput.append(data)

    def errReceived(self, data):
        log.debug("process-err: %s" % (str(data)))
        self.errOutput.append(data)

    def processEnded(self, status_object):
        log.debug("process ended: %s" % str(status_object))
        self.handler.processEnded(status_object)

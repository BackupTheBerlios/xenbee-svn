"""
Implementation of the STOMP protocol (client side)
"""

__version__ = "0.1"
__author__ = "Alexander Petry"

import sys
import time
import re
import socket
import threading
import exceptions
import signal
import codecs

class IllegalTransitionError(exceptions.Exception):
    def __init__(self, state, transition):
        self.state = state
        self.transition = transition
        Exception.__init__(self)
        
    def __str__(self):
        return "%s/%s" % (str(self.state), str(self.transition))

    def __repr__(self):
        return str(self)

class TransactionError(exceptions.Exception):
    pass
class NoTransactionActive(TransactionError):
    pass
        
class State:
    def __init__(self, name="unknown", *args):
        self.name = name
        self.actions = [a for a in args]

    def isAvailable(self, action):
        return action in self.actions

    def availableTransitions(self):
        return self.actions

    def __str__(self):
        return self.name

class StDisconnected(State):
    def __init__(self):
        State.__init__(self, "StDisconnected", "CONNECT", "CONNECTED", "ERROR")

class StConnected(State):
    def __init__(self):
        State.__init__(self, "StConnected"   , "DISCONNECT", "SEND", "SUBSCRIBE", "ACK", "UNSUBSCRIBE", "BEGIN", "ABORT", "COMMIT", "MESSAGE", "RECEIPT", "ERROR")

class Frame:
    """A FRAME as specified by the protocol definition.

    It consists of a verb: CONNECT, DISCONNECT, SUBSCRIBE, etc.
                   header: key: value
                     body: some text terminated by \x00
    """
    def __init__(self, verb, header={}, body=""):
        self.verb = verb
        self.header = header
        self.body = body
        self.header["content-length"] = len(self.body) + len(u"\x00")

    def __str__(self):
        s = [ self.verb ]
        keys = self.header.keys()
        keys.sort()
        for k in keys:
            s.append( u"%s: %s" % (k,self.header.get(k, "")) )
        s.append('')
        if self.body and len(self.body):
            s.append(self.body)
        s.append(u'\x00\x0a')
        return "\n".join(s)
        
class Connection:
    def __init__(self):
        self.ss = None
        self.state = StDisconnected()
        self.buffer = []
        self.mutex = threading.Lock()
        self.additionalHeader = {}
        self.subscriptions = {} # hold information about all subscriptions and if the expect ack messages
        
    def open(self, host='localhost', port=61613):
        self.ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ss.connect((host, port))
        
    def write(self, verb, header, body="", **kwargs):
        if verb not in self.state.availableTransitions():
            raise IllegalTransitionError(self.state, verb)
        header.update(kwargs)
        header.update(self.additionalHeader)

        self.__push( Frame(verb, header, body) )
            
    def __push(self, frame):
        self.mutex.acquire()
        self.buffer.append(frame)
        self.mutex.release()

    def __pop(self):
        self.mutex.acquire()
        f = None
        try:
            f = self.buffer.pop()
        except IndexError:
            pass
        except:
            self.mutex.release()
            raise
        self.mutex.release()
        return f
        
    def flush(self):
        while True:
            f = self.__pop()
            if f: self.__write(f)
            else: break

    def __write(self, frame):
        sys.stdout.write("""*****  sending frame: %s\n%s""" % (time.ctime(), str(frame)))
        sys.stdout.write("""*****\n""")
        sys.stdout.write(str(codecs.getencoder("hex")(str(frame))) + '\n')
        self.ss.sendall( str(frame) )

    def connected(self):
        return self.state.name == "StConnected"

    def __call__(self):
        return self.run()

    def run(self):
        self.ss.settimeout(1)
        self.stopped = False

        recvbuf = []
        while not self.stopped:
            self.flush()
            try:
                recvbuf.append(self.ss.recv(1024))
            except socket.timeout, ti:
                pass
            bytes = ''.join(recvbuf)
            if len(bytes) == 0: continue
                
            if not bytes: continue

            size = len(bytes)
            
            # verb
            verb = None
            try:
                verb = bytes[0:bytes.find('\n')]
                bytes = bytes[len(verb)+1:]
            except:
                raise Exception, 'could not process message (verb parsing)!'
            size -= len(verb)

            # parse header information until a newline is on a single line
            hdr = {}
            while True:
                idx = bytes.find('\n')
                if idx < 0:
                    raise Exception, "no newline in line"
                line = bytes[0:idx]
                size -= idx
                bytes = bytes[idx+1:]
                if not len(line):
                    # found end of header
                    break
                k,v = line.split(':', 1)
                k = k.strip()
                v = v.strip()
                hdr[k] = v

            neededBytes = 0
            if "content-length" in hdr.keys():
                neededBytes = int(hdr["content-length"])

            body = ''
            if neededBytes:
                body  = bytes[0:neededBytes-1]
                bytes = bytes[neededBytes:]
            else:
                if bytes.find('\x00') < 0:
                    raise exceptions.NotImplementedError, "long messages not yet implemented"
                body = bytes[0:bytes.find('\x00')-1]
                bytes = bytes[bytes.find('\x00'):]

            if bytes[0] != '\x00':
                # no correct end found
                raise Exception, "no null-terminated string found"
            recvbuf = []
            if len(bytes) > 1:
                bytes = bytes[1:].strip()
                recvbuf.append(bytes)


            rcvframe = Frame(verb, hdr, body)
            sys.stdout.write("""*****  receiving frame: %s\n%s""" % (time.ctime(), str(rcvframe)))
            sys.stdout.write("""*****\n""")
            sys.stdout.write(str(codecs.getencoder("hex")(str(rcvframe))) + '\n')

            # handle frame
            if verb not in self.state.availableTransitions():
                raise IllegalTransitionError(self.state, verb)
            if verb == "CONNECTED":
                self.state = StConnected()
            if verb == "MESSAGE":
                dest = rcvframe.header["destination"]
                info = self.subscriptions.get(dest, { "reliable": False })
                if info["reliable"] == "client":
                    self.ack(rcvframe.header["message-id"])
            if verb == "RECEIPT":
                msgid = rcvframe.header["receipt-id"]
                print "got acknowledge for", msgid
            if verb == "ERROR":
                print "an error occured:", rcvframe.header["message"]

            if self.state.name == "StDisconnected":
                break
        self.flush()
        self.ss = None

    # protocol methods
    def connect(self, user='', passcode=''):
        self.write(verb="CONNECT", header={}, body="", login=user, passcode=passcode)
        # start thread
        self.worker = threading.Thread(target=self, name="listener")
        self.worker.start()
        
    def send(self, destination, msg, reliable=False):
        if not reliable:
            self.write("SEND", {}, msg, destination=destination)
        else:
            msgid = "msg-" + str(time.time())
            self.write("SEND", {}, msg, destination=destination, receipt=msgid)
            
    def begin(self, transaction):
        if "transaction" in self.additionalHeader.keys():
            raise TransactionError, "attemted to create a transaction in another transaction"
        self.additionalHeader["transaction"] = transaction
        self.write(verb="BEGIN", header={})

    def abort(self):
        if "transaction" not in self.additionalHeader.keys():
            # nothing to abort maybe raise exception
            raise NoTransactionActive, "no transaction is currently active!"
        self.write("ABORT", {})
        self.additionalHeader.pop("transaction")

    def commit(self):
        if "transaction" not in self.additionalHeader.keys():
            raise NoTransactionActive, "no transaction is currently active!"
        self.write("COMMIT", {})
        self.additionalHeader.pop("transaction")

    def subscribe(self, destination, reliable=False):
        destination = destination.strip()
        ack = "auto"
        if reliable:
            ack = "client"
        self.subscriptions[destination] = { "reliable": ack }
        self.write("SUBSCRIBE", {}, destination=destination, ack=ack)

    def unsubscribe(self, destination):
        self.subscriptions.pop(destination)
        self.write("UNSUBSCRIBE", {}, destination=destination)

    def disconnect(self):
        self.write("DISCONNECT", {})
        self.state = StDisconnected()
        self.stopped = True

    def ack(self, msgid):
        self.write(verb="ACK", body="", header={ "message-id":msgid})
    
def selftest(host="localhost", port=6666):
    conn = Connection()
    try:
        def sigint(id,stack):
            conn.stopped = True
        signal.signal(signal.SIGINT, sigint)
        conn.open(host, port)
        conn.connect()
        time.sleep(1)
        conn.subscribe("/queue/a", reliable=False)
        #        conn.begin("tx-1")
        for i in xrange(0, 3):
            conn.send("/queue/a", "123456789-%d" % i, True)
            time.sleep(1)
#        conn.commit()
#        conn.ack("msg-1")
#        time.sleep(4)
        conn.disconnect()
    except KeyboardInterrupt, ki:
        conn.stopped = True

if __name__ == "__main__":
    selftest("localhost", 61613)
    

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

"""Commands used by the commandline tool"""

import logging, sys, re, time, os, uuid, os.path, threading
log = logging.getLogger(__name__)

from optparse import OptionParser
from ConfigParser import ConfigParser

from textwrap import dedent
from xbe.util.singleton import Singleton

class NoPrintOptionParser(OptionParser):
    def __init__(self, usage=None, add_help_option=True):
        OptionParser.__init__(self,usage=usage, add_help_option=add_help_option, prog="")
    def error(self, msg):
        raise CommandFailed(msg)

class CommandFailed(Exception):
    pass

class UnknownCommand(Exception):
    pass

class CommandFactory(Singleton):

    def __init__(self):
        Singleton.__init__(self)
        self.__commands = {}

    def registerCommand(self, cmd, *cmd_names):
        if not self.__commands.has_key(cmd):
            self.__commands[cmd] = [n for n in cmd_names]
        else:
            self.__commands[cmd].extend(cmd_names)

    def lookupCommand(self, name):
        for cmd, names in self.__commands.iteritems():
            if name in names:
                return cmd
        raise LookupError("no command registered with that name", name)

    def getCommands(self):
        return self.__commands

class Command(object):
    """The base class for commands."""

    def pre_execute(self):
        self.opts, self.args = self.parser.parse_args(self.argv)

    def execute(self):
        self._execute()

    def _execute(self):
        """run the specified command."""
        raise RuntimeError("can't execute the base Command.")

    def post_execute(self):
        pass

    def done(self):
        """execution finished."""
        pass

    def failed(self, exception):
        self.mtx.acquire()
        try:
            self.status_info = (True, exception)
        finally:
            self.mtx.release()

    def __init__(self, argv):
        """initialize the command.

        argv -- the arguments passed to this command.

        """
        self.mtx = threading.RLock()
        self.status_info = (False, '')
        self.name = argv[0]
        self.argv = argv[1:]

        p = NoPrintOptionParser(usage="usage: %s [options]" % self.name, add_help_option=False)
        p.add_option("-v", "--verbose",
                     dest="verbose", action="store_true",
                     help="be verbose",
                     default=False)
        p.add_option("-c", "--config",
                     dest="config", default=os.path.expanduser("~/.xbe/xberc"),
                     help="config file to use, default: %default")
        self.parser = p

    def buildHelp(self):
        from StringIO import StringIO
        help_file = StringIO()
        self.parser.print_help(help_file)
        help_file.seek(0)
        lines = help_file.readlines()[2:]
        self.__doc__ += "".join(lines)

    def __str__(self):
        return self.name

from xbe.cmdline.protocol import SimpleCommandLineProtocol

class RemoteCommand(Command, SimpleCommandLineProtocol):
    def __init__(self, argv):
        """Initialize some common options for remote commands."""
        Command.__init__(self, argv)
        p = self.parser
        p.add_option("-T", "--timeout",
                     dest="timeout", type="float",
                     help="number of seconds to wait for an answer from server")
        p.add_option("--user-cert",
                     dest="user_cert",  type="string",
                     help="the certificate to use")
        p.add_option("--user-key",
                     dest="user_key",  type="string",
                     help="the private key to use")
        p.add_option("--ca-cert",
                     dest="ca_cert",  type="string",
                     help="the certificate of the CA")
        p.add_option("-q", "--queue",
                     dest="queue", type="string",
                     help="the queue to connect to")
        p.add_option("-B", "--broker-queue",
                     dest="broker_queue", type="string",
                     help="the broker queue to connect to")
        p.add_option("-S", "--server",
                     dest="server", type="string",
                     help="the server to connect to")
        p.add_option(
            "--stomp-user", dest="stomp_user", type="string",
            help="username for the stomp connection")
        p.add_option(
            "--stomp-pass", dest="stomp_pass", type="string",
            help="password for the stomp connection")

    def __call__(self, *args, **kw):
        """We need to callable, so that we can act as a protocol factory."""
        return self

    def pre_execute(self):
#        try:
#            import optcomplete
#        except ImportError:
#            # no optcompletion available
#            pass
#        else:
#            optcomplete.autocomplete(self.parser)
        self.mtx.acquire()
        try:
            opts, args = self.parser.parse_args(self.argv)
            self.__pre_parse(opts, args)
            self.check_opts_and_args(opts, args)
            self.opts, self.args = opts, args
            self.buildHelp()
        finally:
            self.mtx.release()
        self.setUp()

    def post_execute(self):
        self.tearDown()

    def __pre_parse(self, opts, args):
        cp = ConfigParser()
        self.cp = cp
        read_files = cp.read([os.path.join(os.environ.get("XBE_HOME", "/"), "etc", "xbe", "xberc"),
#                              os.path.expanduser(os.path.join(self.__home, "etc", "xbe", "xberc")),
                              os.path.expanduser("~/.xbe/xberc"),
                              opts.config])
        if not len(read_files):
            raise CommandFailed("no configuration file found")
        
        if opts.timeout is None:
            opts.timeout = cp.getfloat("network", "timeout")
        if opts.queue is None:
            opts.queue = cp.get("network", "queue")
        if opts.broker_queue is None:
            opts.broker_queue = cp.get("network", "broker_queue")
        if opts.server is None:
            opts.server = cp.get("network", "server")
        if opts.stomp_user is None:
            opts.stomp_user = cp.get("network", "user")
        if opts.stomp_pass is None:
            opts.stomp_pass = cp.get("network", "pass")

        if opts.user_cert is None:
            opts.user_cert = os.path.expanduser(cp.get("security", "pubkey"))
        if opts.user_key is None:
            opts.user_key = os.path.expanduser(cp.get("security", "privkey"))
        if opts.ca_cert is None:
            opts.ca_cert = os.path.expanduser(cp.get("security", "cacert"))

        from xbe.xml.security import X509Certificate
        # build the certificate
        self.user_cert = X509Certificate.load_from_files(opts.user_cert,
                                                         opts.user_key)
        self.ca_cert = X509Certificate.load_from_files(opts.ca_cert)

    def connectionMade(self):
        log.info("connection made")
        self.cancelTimeout()
        try:
            self.execute()
        except Exception, e:
            self.failed(e)

    def cancelTimeout(self):
        self.mtx.acquire()
        try:
            to = self.__timeoutCall
            del self.__timeoutCall
            to.cancel()
#            log.debug("timeout -")
        except AttributeError:
            pass
        finally:
            self.mtx.release()

    def execute(self):
        try:
            self.scheduleTimeout()
            rv = self._execute()
#            self.cancelTimeout()
        except Exception, e:
            self.failed(e)
        else:
            if rv:
                self.done()

    def scheduleTimeout(self, timeout=None, *args, **kw):
        self.mtx.acquire()
        try:
            self.cancelTimeout()
            from twisted.internet import reactor
            if timeout is None:
                timeout = self.opts.timeout
            self.__timeoutCall = reactor.callLater(timeout,
                                                   self.timedout, *args, **kw)
#            log.debug("timeout +")
        finally:
            self.mtx.release()

    def timedout(self, name=None):
        self.mtx.acquire()
        try:
            del self.__timeoutCall
            msg = "timed out"
            if name is not None:
                msg = "%s %s" % (name, msg)
#            log.debug("timeout !")
            self.failed(RuntimeError(msg))
        finally:
            self.mtx.release()

    def stop(self, failed=False, *args, **kw):
        from twisted.internet import reactor
        if failed:
            reactor.callLater(0.00001, self.failed, *args, **kw)
        else:
            reactor.callLater(0.00001, self.done, *args, **kw)
        reactor.wakeUp()

    def done(self):
        self.mtx.acquire()
        try:
            self.cancelTimeout()
            from twisted.internet import reactor
            log.debug("stopping")
            Command.done(self)
            reactor.stop()
        finally:
            self.mtx.release()

    def failed(self, exception):
        self.mtx.acquire()
        try:
            self.cancelTimeout()
            from twisted.internet import reactor
            reactor.stop()
            Command.failed(self, exception)
        finally:
            self.mtx.release()

    def errorReceived(self, error):
        self.cancelTimeout()
        from xbe.xml import errcode
        
        code = error.code()
        desc = error.description()
        name = error.name()
        msg  = error.message()
        
        print "%d [%s] (%s) - %s" % (
            code, name, desc, msg
        )

        if code == errcode.OK:
            self.stop()
        else:
            self.stop(True, RuntimeError(error.description()))

    #########################################
    #                                       #
    # Override these methods in a subclass  #
    #                                       #
    #########################################
    def check_opts_and_args(self, opts, args):
        pass
    
    def setUp(self):
        pass
    
    def _execute(self):
        raise CommandFailed("please implement me")

    def tearDown(self):
        pass

    def bookedResponseReceived(self, bookingInformation):
	log.info("====================RemoteCommand::bookedResponseReceived")
        #msg = message.ConfirmReservation(ticket, jsdl, auto_start)
        pass

class HasTicket:
    def __init__(self, parser):
        p = parser
        if not p.has_option("-t"):
            p.add_option("-t", "--ticket", dest="ticket",
                         type="string", help="the ticket of the reservation")
        self.parser = p

    def get_ticket(self):
        if not hasattr(self.opts, "ticket") or self.opts.ticket is None:
            raise ValueError("no ticket")
        else:
            ticket = self.opts.ticket
        return ticket

class HasUuid:
    def __init__(self, parser):
        p = parser
        if not p.has_option("-U"):
            p.add_option("-U", "--uuid", dest="uuid",
                         type="string", help="the client uuid used during the booking request")
        self.parser = p

    def get_uuid(self):
        if not hasattr(self.opts, "uuid") or self.opts.uuid is None:
            raise ValueError("no uuid")
        else:
            uuid = self.opts.uuid
        return uuid

## Calana extensions
class BrokerCommand(RemoteCommand):
    def __init__(self, argv):
        """Initialize some common options for broker commands."""
        RemoteCommand.__init__(self, argv)

    def _execute(self):
        log.info("BrokerCommand::_execute")
        self.scheduleTimeout(name="ping")
        self.pingRequest()
        return False

    def pollResponseReceived(self, msg):
        log.info("BrokerCommand::pollResponseReceived (%s)" % msg.cmd_name())
        #tag = 
        self.scheduleTimeout(name="ping")
        #self.pingRequest()
        time.sleep(2)
        self.pollRequest( msg.cmd_name() )
        return False

    def bookedResponseReceived(self, bookingInformation):
	log.info("====================BrokerCommand::bookedResponseReceived")
        #msg = message.ConfirmReservation(ticket, jsdl, auto_start)
        pass

class Command_help(Command):
    """\
    help: Describe the usage of this program or its subcommands.

    usage: help [subcommand]
    Valid options:
         currently none
    """
    def __init__(self, argv):
        """initialize the 'help' command."""
        Command.__init__(self, argv)
        self.subcmd = createCommand(self.argv)
        
    def _execute(self):
        if self.subcmd:
            print >>sys.stderr, dedent(self.subcmd.__doc__).strip()
        else:
            sb = [dedent(__doc__).strip()]
            sb.append("")
            sb.append("available subcommands:")
            sb.append("")
            cmds = CommandFactory.getInstance().getCommands()
            cmdnames = cmds.values()
            cmdnames.sort(lambda a,b: cmp(a[0], b[0]))
            for names in cmdnames:
                line = names[0]
                if len(names) > 1:
                    line += " (" + ", ".join(names[1:]) + ")"
                sb.append("   "+line)
            print >>sys.stderr, "\n".join(sb)
CommandFactory.getInstance().registerCommand(Command_help, "help", "h", "?")

class Command_reserve(RemoteCommand):
    """\
    reserve: make a reservation

    """
    def __init__(self, argv = []):
        """initialize the 'create' command."""
        RemoteCommand.__init__(self, argv)

    def _execute(self):
        self.scheduleTimeout(name="reserve")
        self.requestReservation()
        return False

    def reservationResponseReceived(self, reservationResponse):
        self.cancelTimeout()
        self.ticket = reservationResponse.ticket()
        self.task = reservationResponse.task_id()
        self.print_info(self.ticket, self.task)
        self.madeReservation(self.ticket, self.task)

    def print_info(self, ticket, task):
        print dedent("""\
        ticket:%(ticket)s
        task:%(task)s
        """ % {"ticket": ticket,
               "task": task,
               }
        )

    def madeReservation(self, ticket, task):
        self.stop()
CommandFactory.getInstance().registerCommand(Command_reserve, "reserve", "res")

class Command_terminate(RemoteCommand, HasTicket):
    """\
    terminate (tr): Terminate the task belonging to some ticket.
    """

    def __init__(self, argv):
        """initialize the 'terminate' command."""
        RemoteCommand.__init__(self, argv)
        HasTicket.__init__(self, self.parser)
        
    def check_opts_and_args(self, opts, args):
        if opts.ticket is None:
            if len(args):
                opts.ticket = args.pop(0)
            else:
                raise CommandFailed("ticket required")
        return True

    def _execute(self):
        ticket = self.get_ticket()
        self.requestTermination(ticket)
        return False
CommandFactory.getInstance().registerCommand(Command_terminate,
                                             "terminate", "term", "kill", "cancel")

class Command_cache(RemoteCommand):
    """\
    cache: Cache a given file in the server's cache.
    """

    def __init__(self, argv):
        """initialize the 'cache' command."""
        RemoteCommand.__init__(self, argv)
        p = self.parser
        p.add_option("-u", "--uri", dest="uri", type="string",
                     help="the uri which is to be cached")
        p.add_option("--type", dest="type", type="string", default="data",
                     help="the type of the file (default: %default)")
        p.add_option("--desc", dest="desc", type="string",
                     help="some description")
        
    def check_opts_and_args(self, opts, args):
        if opts.uri is None:
            if len(args):
                opts.uri = args.pop(0)
            else:
                raise CommandFailed("uri required")

        if opts.desc is None:
            if len(args):
                opts.desc = args.pop(0)
            else:
                opts.desc = "Not available"
        return True
    
    def _execute(self):
        self.cacheFile(self.opts.uri, self.opts.type, self.opts.desc)
        print >>sys.stderr, "waiting for response from server..."
        return False
CommandFactory.getInstance().registerCommand(Command_cache, "cache")

class Command_remove(RemoteCommand):
    """\
    remove: Removes a cache entry on the server.
    """

    def __init__(self, argv):
        """initialize the 'cache' command."""
        RemoteCommand.__init__(self, argv)
        p = self.parser
        p.add_option("-u", "--uri", dest="uri", type="string",
                     help="the uri of the cache entry.")
        
    def check_opts_and_args(self, opts, args):
        if opts.uri is None:
            if len(args):
                opts.uri = args.pop(0)
            else:
                raise CommandFailed("cache uri required")
        return True
    
    def _execute(self):
        self.cacheRemove(self.opts.uri)
        return False
CommandFactory.getInstance().registerCommand(Command_remove, "remove", "uncache", "rc")

class Command_start(RemoteCommand, HasTicket):
    """\
    start: Start a given reservation.
    """

    def __init__(self, argv):
        """initialize the 'start' command."""
        RemoteCommand.__init__(self, argv)
        HasTicket.__init__(self, self.parser)
        
    def check_opts_and_args(self, opts, args):
        if opts.ticket is None:
            if len(args):
                opts.ticket = args.pop(0)
            else:
                raise CommandFailed("ticket required")
        return True

    def _execute(self):
        ticket = self.get_ticket()
        self.requestStart(ticket)
        return False
CommandFactory.getInstance().registerCommand(Command_start, "start")

#class Command_confirm(BrokerCommand, HasUuid, Command_terminate):
class Command_confirm(BrokerCommand, HasUuid, HasTicket):
    """\
    confirm: confirm a previously made reservation

    """
    def __init__(self, argv = []):
        """initialize the 'confirm' command."""
        BrokerCommand.__init__(self, argv)
        #Command_terminate.__init__(self, argv)
        HasTicket.__init__(self, self.parser)
        HasUuid.__init__(self, self.parser)
        
        p = self.parser
        p.add_option("-x", "--xsdl", dest="xsdl",  type="string",
                     help="the xsdl document to submit or %default")
        p.add_option("--schema-dir", dest="schema_dir", type="string",
                     help="path to a directory, containing required xsd schema definitions.")
        
    def check_opts_and_args(self, opts, args):
        #Command_terminate.check_opts_and_args(self, opts, args)
        #HasTicket.check_opts_and_args(self, opts, args)
        #HasUuid.check_opts_and_args(self, opts, args)
        if opts.uuid is None:
            if len(args):
                opts.uuid = args.pop(0)
            else:
                raise CommandFailed("uuid required")
        if opts.ticket is None:
            if len(args):
                opts.ticket = args.pop(0)
            else:
                raise CommandFailed("ticket required")
        if opts.xsdl is None:
            if len(args):
                opts.xsdl = args.pop(0)
            else:
                opts.xsdl = "-"
        if opts.schema_dir is None:
            opts.schema_dir = os.path.expanduser(self.cp.get("global", "schema_dir"))
        return True
    
    def _execute(self):
        ticket = self.get_ticket()
        try:
            self.read_schema_documents()
            self.scheduleTimeout(name="file reading failed", timeout=10)
            xsdl = self.get_xsdl()
            self.cancelTimeout()
            self.scheduleTimeout(name="server seems down", timeout=60)
            self.confirmReservation(ticket, xsdl)
        except Exception, e:
            print repr(e)
#            print "cancelling reservation %s" % ticket
#            Command_terminate._execute(self)
            raise
        return True

    def get_xsdl(self, path=None):
        if path is None:
            if not hasattr(self.opts, "xsdl"):
                if len(self.args) > 0:
                    path = self.args.pop(0)
                else:
                    raise ValueError("no path given to read xsdl from")
            else:
                path = self.opts.xsdl
                
        if path == "-":
            print >>sys.stderr, "reading from stdin..."
            f = sys.stdin
        else:
            f = open(path, 'rb')
        return self.read_xsdl(f)

    def read_schema_documents(self):
        log.info("initializing schema documents...")
        from lxml import etree
        self.schema_map = {}
        for schema in os.listdir(self.opts.schema_dir):
            if not schema.endswith(".xsd"): continue
            path = os.path.join(self.opts.schema_dir, schema)
            log.info("   reading %s" % path)
            xsd_doc = etree.parse(path)
            namespace = xsd_doc.getroot().attrib["targetNamespace"]
            self.schema_map[namespace] = etree.XMLSchema(xsd_doc)
        log.info("  done.")
        return self.schema_map
    
    def read_xsdl(self, f):
        from lxml import etree
        xsdl = etree.parse(f).getroot()
        from xbe.xml.jsdl import JsdlDocument
        try:
            doc = JsdlDocument(self.schema_map)
            doc.parse(xsdl)
        except Exception, e:
            raise CommandFailed("document invalid", e)
        return xsdl
CommandFactory.getInstance().registerCommand(Command_confirm, "confirm")
        
class Command_submit(Command_reserve, Command_confirm):
    """\
    create: Submit a new task.

    """

    def __init__(self, argv = []):
        """initialize the 'submit' command.

        this command uses the interface provided by Command_reserve
        and Command_confirm to fulfill its task.
        """
        Command_confirm.__init__(self, argv)

    def check_opts_and_args(self, opts, args):
        if opts.xsdl is None:
            if len(args):
                opts.xsdl = args.pop(0)
            else:
                opts.xsdl = "-"
        if opts.schema_dir is None:
            opts.schema_dir = os.path.expanduser(self.cp.get("global", "schema_dir"))
    
    def _execute(self):
        if self.opts.xsdl != "-" and not os.path.exists(self.opts.xsdl):
            raise CommandFailed("file not found: %s" % self.opts.xsdl)
        Command_reserve._execute(self)
        return False

    def get_ticket(self):
        return self.ticket

    def madeReservation(self, ticket, task):
        self.ticket = ticket
        self.task = task
        Command_confirm._execute(self)
CommandFactory.getInstance().registerCommand(Command_submit, "submit", "sub", "s")

class Command_status(RemoteCommand, HasTicket):
    """\
    status: Request status information

    """

    def __init__(self, argv):
        """initialize the 'status' command."""
        RemoteCommand.__init__(self, argv)
        HasTicket.__init__(self, self.parser)
        p = self.parser
        p.add_option("-r", "--remove", dest="remove_entry", action="store_true", default=False,
                     help="remove the status entry, if it has finished")
        p.add_option("-x", "--execute-status-task", dest="execute_status_task", action="store_true", default=False,
                     help="request execution of the status-task at the remote location")

    def check_opts_and_args(self, opts, args):
        if opts.ticket is None:
            if len(args):
                opts.ticket = args.pop(0)
            else:
                opts.ticket = "all"
                #raise CommandFailed("ticket required")
        return True
    
    def _execute(self):
        ticket = self.get_ticket()
        self.scheduleTimeout(name="status-request")
        self.requestStatus(ticket, self.opts.remove_entry, self.opts.execute_status_task)
        return False

    def statusListReceived(self, statusList):
        self.cancelTimeout()
        if self.opts.verbose:
            print repr(statusList)
        else:
            try:
                for k,v in statusList.entries().iteritems():
                    print "ticket:%s - task:%s - %s" % (v["Ticket"], k, v["State"])
            except:
                print "status retrieval failed"
                sys.exit(1)
        self.stop()
CommandFactory.getInstance().registerCommand(Command_status, "status", "stat", "st")

class Command_showcache(RemoteCommand):
    """\
    showcache (sc): show cache entries

    """

    def __init__(self, argv):
        """initialize the 'status' command."""
        RemoteCommand.__init__(self, argv)

    def _execute(self):
        self.scheduleTimeout(name="show-cache")
        self.requestCacheList()
        return False

    def cacheEntriesReceived(self, cache_entries):
        self.cancelTimeout()
        print repr(cache_entries)
        self.stop()
CommandFactory.getInstance().registerCommand(Command_showcache, "showcache", "sc")

## Calana extensions

class Command_pingpong(BrokerCommand):
    """\
    ping: make a ping request

    """
    def __init__(self, argv = []):
        """initialize the 'create' command."""
        BrokerCommand.__init__(self, argv)

    def _execute(self):
        log.info("Command_pingpong::_execute")
        self.scheduleTimeout(name="ping")
        self.pingRequest()
        return False

    def pongResponseReceived(self, pongmsg):
        log.info("Command_pingpong::Pong c=%s" % pongmsg.count())
        print "Pong c=%s" % pongmsg.count()
        #        self.ticket = reservationResponse.ticket()
        #        self.task = reservationResponse.task_id()
        #        self.print_info(self.ticket, self.task)
        #        self.madeReservation(self.ticket, self.task)
        self.stop()

    def print_info(self, ticket, task):
        print dedent("""\
        ticket:%(ticket)s
        task:%(task)s
        """ % {"ticket": ticket,
               "task": task,
               }
        )
CommandFactory.getInstance().registerCommand(Command_pingpong, "ping")


class Command_bookingreq(BrokerCommand):
    """\
    bookingrequest: make a bookingRequest

    """
    def __init__(self, argv = []):
        """initialize the 'create' command."""
        BrokerCommand.__init__(self, argv)
        self.__ticket  = None
        
    def _execute(self):
        self.scheduleTimeout(name="bookingreq")
        self.bookingRequest()
        log.info("Command_bookingreq::bookedResponseReceived DONE, next command")
        return False

    def bookedResponseReceived(self, reservationResponse):
        log.info("Command_bookingreq::bookedResponseReceived")
        self.print_info(reservationResponse.ticket(), reservationResponse.task_id(),
                   reservationResponse.uuid(),  reservationResponse.xbedurl(),
	           reservationResponse.price())
        self.__ticket = reservationResponse.ticket()
        # no send confirm

        self.madeReservation(reservationResponse.ticket(), reservationResponse.task_id(),
                   reservationResponse.uuid(),  reservationResponse.xbedid())
        self.stop()
        return True

    def print_info(self, ticket, task, uuid, xbeid, price):
        print dedent("""\
        ticket:%(ticket)s
        task  :%(task)s
        """ % {"ticket": ticket,
               "task": task,
               }
        )
        print "Reservation Ticket  : %s" % ticket
        print "Reservation task-id : %s" % task
        print "Reservation my-id   : %s" % uuid
        print "Reservation serverid: %s" % xbeid
        print "Price per minute    : %5.2f " % price
        #print "confirm  : xbe bc -t %s -U %s" % (ticket, uuid)
        print "jobstatus: xbe jobstatus -t %s -U %s" % (ticket, uuid)
        print "status   : xbe st -q %s" % (xbeid)
        print "start    : xbe start -q %s -t %s" % (xbeid, ticket)

    def madeReservation(self, ticket, task, uuid, xbeid):
        self.ticket = ticket
        self.task   = task
        #Command_confirm._execute(self)

CommandFactory.getInstance().registerCommand(Command_bookingreq, "bookingreq", "book")


#class Command_bookedconfirm(BrokerCommand, HasUuid, HasTicket): #, Command_confirm):
#    """\
#    bookingrequest: confirm a booking response
#
#    """
#    def __init__(self, argv = []):
#        """initialize the 'create' command."""
#        BrokerCommand.__init__(self, argv)
#        #Command_confirm.__init__(self, self.parser)
#        HasUuid.__init__(self, self.parser)
#
#        #p = self.parser
#        #if not p.has_option("-U"):
#        #    p.add_option("-U", "--uuid", dest="uuid",  type="string",
#        #                 help="uuid from session")
#        #self.parser = p
#
#        #Command_confirm.__init__(self, argv)
#        #self.__uuid    = None
#        #self.__ticket  = None
#        #self.__task_id = None
#        
#    def check_opts_and_args(self, opts, args):
#        #Command_terminate.check_opts_and_args(self, opts, args)
#        if opts.ticket is None:
#            if len(args):
#                opts.ticket = args.pop(0)
#            else:
#                raise CommandFailed("ticket required")
#        if opts.uuid is None:
#            if len(args):
#                opts.uuid = args.pop(0)
#            else:
#                raise CommandFailed("uuid required")
#        return True
#
#    def _execute(self):
#        self.scheduleTimeout(name="bookconfirm")
#        task_id="none"
#        self.bookedConfirm(self.get_uuid(), self.get_ticket(), task_id)
#        log.info("Command_bookedconfirm::bookedResponseReceived DONE, next command")
#        return False
#
#    def bookedResponseReceived(self, reservationResponse):
#        log.info("Command_bookedconfirm::bookedResponseReceived")
#        self.stop()
#        return True
#
#    def print_info(self, ticket, task, uuid, xbeid, price):
#        print dedent("""\
#        ticket:%(ticket)s
#        task  :%(task)s
#        """ % {"ticket": ticket,
#               "task": task,
#               }
#        )
#        print "Reservation Ticket  : %s" % ticket
#        print "Reservation task-id : %s" % task
#        print "Reservation my-id   : %s" % uuid
#        print "Reservation serverid: %s" % xbeid
#        print "Price per minute    : %5.2f " % price
#
#    def madeReservation(self, ticket, task, uuid, xbeid):
#        self.ticket = ticket
#        self.task   = task
#        #Command_confirm._execute(self)
#
#CommandFactory.getInstance().registerCommand(Command_bookedconfirm, "bookconfirm", "bc")

class Command_jobstatusreq(BrokerCommand, HasUuid, HasTicket):
    """\
    jobstatusrequest: make a job status Request

    """
    def __init__(self, argv = []):
        """initialize the 'create' command."""
        BrokerCommand.__init__(self, argv)
        HasTicket.__init__(self, self.parser)
        HasUuid.__init__(self, self.parser)
        self.__ticket  = None
        
    def check_opts_and_args(self, opts, args):
        #Command_terminate.check_opts_and_args(self, opts, args)
        #HasTicket.check_opts_and_args(self, opts, args)
        #HasUuid.check_opts_and_args(self, opts, args)
        if opts.uuid is None:
            if len(args):
                opts.uuid = args.pop(0)
            else:
                raise CommandFailed("uuid required")
        if opts.ticket is None:
            if len(args):
                opts.ticket = args.pop(0)
            else:
                raise CommandFailed("ticket required")
        return True

    def _execute(self):
        self.scheduleTimeout(name="jobstatusreq")
        self.jobstatusRequest(self.get_uuid(), self.get_ticket(), "none")
        log.info("Command_jobstatusreq::statusResponseReceived DONE, next command")
        return False

    def jobstatusResponseReceived(self, statusResponse):
        log.info("Command_jobstatusreq::statusResponseReceived")
        self.print_info(statusResponse.ticket(), statusResponse.task_id(),
                        statusResponse.time(), statusResponse.cost(),
                        statusResponse.start(), statusResponse.end(),statusResponse.state() )
        self.__ticket = statusResponse.ticket()
        # no send confirm
        self.stop()
        return True

    def print_info(self, ticket, task, time, cost, start, end, state):
        print dedent("""\
        ticket:%(ticket)s
        task  :%(task)s
        """ % {"ticket": ticket,
               "task": task,
               }
        )
        print "Reservation Ticket  : %s" % ticket
        print "Reservation task-id : %s" % task
        print "Job State           : %s" % state
        print "Time start          : %5.2f sec " % start
        print "Time end            : %5.2f sec " % end
        print "Time used           : %5.2f sec " % time
        print "Total cost          : %5.2f " % cost

CommandFactory.getInstance().registerCommand(Command_jobstatusreq, "jobstatus", "jst")

## Calana extensions


class CommandLineClient:
    def __init__(self,home,out=sys.stdout,err=sys.stderr):
	self.__home = home
        self.__old_out, sys.stdout = sys.stdout, out
        self.__old_err, sys.stderr = sys.stderr, err

    def __del__(self):
        sys.stdout = self.__old_out
        sys.stderr = self.__old_err

    def setup_logging(self, verbose=False):
        if verbose:
            print >>sys.stderr, "setting up logging..."
        # log to stderr
        logging.currentframe = lambda: sys._getframe(3)
        
        _stderr = logging.StreamHandler(sys.stderr)
        if verbose:
            _stderr.setLevel(logging.DEBUG)
            logging.getLogger('').setLevel(logging.DEBUG)
        else:
            _stderr.setLevel(logging.ERROR)
            logging.getLogger('').setLevel(logging.DEBUG)
        _stderr.setFormatter(logging.Formatter('%(name)s:%(lineno)d: %(levelname)-8s %(message)s'))
        logging.getLogger('').addHandler(_stderr)

    def printShortHelp(self):
        print >>sys.stderr, "Type '%s help' for usage." % self.argv[0]

    def main(self, argv=sys.argv, prog_name=None):
        from twisted.python import threadable
        threadable.init()

        if prog_name is None:
            argv[0] = os.path.basename(argv[0])
        self.argv = argv

        cmd = createCommand(argv[1:])
        if cmd:
            try:
                cmd.pre_execute()
                self.setup_logging(cmd.opts.verbose)

                if isinstance(cmd, RemoteCommand):
                    from xbe.util import network
                    server = cmd.opts.server
                    #prot, host, stomp_queue, u1, u2, u3 = network.urlparse(server)
                    prot, host, stomp_queue, u1, u2, u3 = network.urlparse(server)
                    if isinstance(cmd, BrokerCommand):
                        stomp_queue = cmd.opts.broker_queue
                    else:
                        stomp_queue = cmd.opts.queue

                    if prot != "stomp":
                        raise ValueError("I do not understand this wire-protocol", prot)
                    log.debug("connecting to: %s" % server)
                    from xbe.cmdline.protocol import ClientProtocolFactory, ClientXMLProtocol
                    # TODO: generate ID or use some given one
                    if hasattr(cmd, "get_uuid"):
                        client_id = getattr(cmd , "get_uuid")()
                        pass
                    else:
                        client_id=str(uuid.uuid4())
                    factory = ClientProtocolFactory(
                        id = client_id,
                        stomp_user=cmd.opts.stomp_user, stomp_pass=cmd.opts.stomp_pass,
                        certificate=cmd.user_cert, ca_cert=cmd.ca_cert,
                        server_queue="/queue/"+stomp_queue,
                        protocolFactory=ClientXMLProtocol,
                        protocolFactoryArgs=(cmd,))
                    
                    from twisted.internet import reactor
                    from twisted.python import threadable
                    threadable.init()

                    h_p = host.split(":")
                    if len(h_p) == 2:
                        host, port = h_p
                    else:
                        host, port = h_p[0], 61613
                    # schedule a Timeout
                    cmd.scheduleTimeout(name="connect")
                    reactor.connectTCP(host, port, factory)
                    reactor.run()
                else:
                    cmd.execute()
                cmd.post_execute()
                if cmd.status_info[0]:
                    raise CommandFailed(cmd.status_info[1])
            except CommandFailed, cf:
                print >>sys.stderr, "%s:" % sys.argv[0], str(cmd), "failed (details follow)"
                print >>sys.stderr, "\n".join([ "%s: %s" %
                                                (sys.argv[0],s) for s in str(cf).split('\n')])
                return 2
            except:
                from traceback import format_exc
                print >>sys.stderr, "Error during command execution:", format_exc()
                return 3
        else:
            self.printShortHelp()
            return 1
        return 0

def createCommand(argv):
    """Creates a command object from the given command line."""
    if len(argv):
        try:
            cmdname = argv[0]
            try:
                cmdcls = CommandFactory.getInstance().lookupCommand(cmdname)
            except LookupError:
                raise UnknownCommand(cmdname)
            cmd = cmdcls(argv)
            cmd.buildHelp()
            return cmd
        except UnknownCommand, uc:
            print >>sys.stderr, "Unknown command: '%s'" % uc
            return None
        except:
            from traceback import format_exc
            print >>sys.stderr, "Unknwon error:", format_exc()
            return None
    else:
        return None

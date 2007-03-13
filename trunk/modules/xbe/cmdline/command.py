"""Commands used by the commandline tool"""

import logging, sys, re, os, uuid
log = logging.getLogger(__name__)

from optparse import OptionParser
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
        """run the specified command."""
        raise RuntimeError("can't execute the base Command.")

    def post_execute(self):
        pass

    def done(self):
        """execution finished."""
        pass

    def failed(self, exception):
        self.status_info = (True, exception)

    def __init__(self, argv):
        """initialize the command.

        argv -- the arguments passed to this command.

        """

        self.status_info = (False, '')
        self.name = argv[0]
        self.argv = argv[1:]

        p = NoPrintOptionParser(usage="usage: %s [options]" % self.name, add_help_option=False)
        p.add_option("-v", "--verbose",
                     dest="verbose", action="store_true",
                     help="be verbose",
                     default=False)
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
                     dest="timeout", type="float", default=10,
                     help="number of seconds (default %defaults) to wait for an answer from server")
        p.add_option("--user-cert",
                     dest="user_cert",  type="string",
                     default=os.path.join(os.environ["HOME"], ".xbe", "user.pem"),
                     help="the certificate to use (default: %default)")
        p.add_option("--user-key",
                     dest="user_key",  type="string",
                     default=os.path.join(os.environ["HOME"], ".xbe", "user-key.pem"),
                     help="the private key to use (default: %default)")
        p.add_option("--ca-cert",
                     dest="ca_cert",  type="string",
                     default=os.path.join(os.environ["HOME"], ".xbe", "ca-cert.pem"),
                     help="the certificate of the CA (default: %default)")
        p.add_option("-S", "--server",
                     dest="server", type="string",
                     help="the server to connect to or %default is used",
                     default="stomp://xen-o-matic.itwm.fhrg.fraunhofer.de/queue/xenbee.daemon.1")

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
        opts, args = self.parser.parse_args(self.argv)
        self.__pre_parse(opts, args)
        self.check_opts_and_args(opts, args)
        self.opts, self.args = opts, args
        self.buildHelp()

        self.setUp()

    def post_execute(self):
        self.tearDown()

    def __pre_parse(self, opts, args):
        if opts.user_cert is None:
            opts.user_cert = os.path.join(
                os.environ["HOME"], ".xbe", "user.pem"
            )
        if opts.user_key is None:
            opts.user_key = os.path.join(
                os.environ["HOME"], ".xbe", "user-key.pem"
            )
        if opts.ca_cert is None:
            opts.ca_cert = os.path.join(
                os.environ["HOME"], ".xbe", "ca-cert.pem"
            )

        from xbe.xml.security import X509Certificate
        # build the certificate
        self.user_cert = X509Certificate.load_from_files(opts.user_cert,
                                                         opts.user_key)
        self.ca_cert = X509Certificate.load_from_files(opts.ca_cert)

    def connectionMade(self):
        self.cancelTimeout()
        try:
            self.execute()
        except Exception, e:
            self.cancelTimeout()
            self.failed(e)

    def cancelTimeout(self):
        try:
            to = self.__timeoutCall
        except AttributeError:
            pass
        else:
            del self.__timeoutCall
            to.cancel()

    def scheduleTimeout(self, timeout=None, *args, **kw):
        self.cancelTimeout()
        from twisted.internet import reactor
        if timeout is None:
            timeout = self.opts.timeout
        self.__timeoutCall = reactor.callLater(self.opts.timeout,
                                               self.timeout, *args, **kw)

    def timeout(self, name=None):
        del self.__timeoutCall
        msg = "timed out"
        if name is not None:
            msg = "%s %s" % (name, msg)
        self.failed(RuntimeError(msg))

    def done(self):
        self.cancelTimeout()
        from twisted.internet import reactor
        reactor.callLater(0.5, reactor.stop)
        Command.done(self)

    def failed(self, exception):
        self.cancelTimeout()
        from twisted.internet import reactor
        reactor.callLater(0.5, reactor.stop)
        Command.failed(self, exception)

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

        if code >= errcode.INTERNAL_SERVER_ERROR:
            print "This is a very serious error, bailing out!"
            sys.exit(2)
        if code == errcode.OK:
            self.done()
        else:
            self.failed(RuntimeError(error.description()))

    #########################################
    #                                       #
    # Override these methods in a subclass  #
    #                                       #
    #########################################
    def check_opts_and_args(self, opts, args):
        pass
    
    def setUp(self):
        pass
    
    def execute(self):
        raise CommandFailed("please implement me")

    def tearDown(self):
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
        
    def execute(self):
        if self.subcmd:
            print >>sys.stderr, dedent(self.subcmd.__doc__).strip()
        else:
            sb = [dedent(__doc__).strip()]
            sb.append("")
            sb.append("available subcommands:")
            sb.append("")
            cmds = CommandFactory.getInstance().getCommands()
            for cmd, names in cmds.iteritems():
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

    def execute(self):
        self.scheduleTimeout(name="reserve")
        self.requestReservation()

    def reservationResponseReceived(self, reservationResponse):
        self.cancelTimeout()
        self.ticket = reservationResponse.ticket()
        self.task = reservationResponse.task_id()
        self.print_info(self.ticket, self.task)
        self.madeReservation(self.ticket, self.task)

    def print_info(self, ticket, task):
        print dedent("""\
        Your ticket identification code:
        ================================

        *%(bar1)s*
        *%(bar2)s*
        * %(ticket)s *
        *%(bar2)s*
        *%(bar1)s*

        please remember that ticket-id, it will be
        required in subsequent calls.

        A task has been registered for you as:
        %(task)s
        """ % {"ticket": ticket,
               "task": task,
               "bar1": ("*" * (len(ticket)+2)),
               "bar2": (" " * (len(ticket)+2)),
               }
        )

    def madeReservation(self, ticket, task):
        self.done()
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
    
    def execute(self):
        ticket = self.get_ticket()
        self.requestTermination(ticket)
        self.done()
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
    
    def execute(self):
        self.cacheFile(self.opts.uri, self.opts.type, self.opts.desc)
        print >>sys.stderr, "waiting for response from server..."
CommandFactory.getInstance().registerCommand(Command_cache, "cache")

class Command_confirm(Command_terminate):
    """\
    confirm: confirm a previously made reservation

    """
    def __init__(self, argv = []):
        """initialize the 'confirm' command."""
        Command_terminate.__init__(self, argv)
        
        p = self.parser
        p.add_option("-x", "--xsdl", dest="xsdl",  type="string",
                     help="the xsdl document to submit or %default")

    def check_opts_and_args(self, opts, args):
        Command_terminate.check_opts_and_args(self, opts, args)
        if opts.xsdl is None:
            if len(args):
                opts.xsdl = args.pop(0)
            else:
                opts.xsdl = "-"
        return True
    
    def execute(self):
        ticket = self.get_ticket()
        try:
            xsdl = self.get_xsdl()
            self.confirmReservation(ticket, xsdl)
        except Exception, e:
            print "cancelling reservation %s" % ticket
            Command_terminate.execute(self)
            raise
        self.done()

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
    
    def read_xsdl(self, f):
        from lxml import etree
        xsdl = etree.parse(f).getroot()
        # TODO: validate the xsdl
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

# this has to be moved into some other tool
#
#        p.add_option("-k", "--kernel", dest="kernel",  type="string",
#                     help="the uri to the kernel")
#        p.add_option("-r", "--initrd", dest="initrd",  type="string",
#                     help="the uri to a initrd")
#        p.add_option("-m", "--mem",    dest="memory",  type="int",
#                     help="the amount of memory to use (in MB)", default=128)
#        p.add_option("-s", "--swap",   dest="swap",    type="int",
#                     help="the amount of swap space to use (in MB)", default=128)
#        p.add_option("-i", "--image",  dest="image",   type="string",
#                     help="the main image to boot")
#        p.add_option("-C", "--cpus",   dest="cpus",    type="int",
#                     help="the number of cpus to use", default=1)
#        p.add_option("-j", "--jsdl",   dest="jsdl",    type="string",
#                     help="a jsdl document", default="-")
#        p.add_option("-K", "--keep",   dest="keep_instance", action="store_true",
#                     help="a jsdl document", default=False)

    def check_opts_and_args(self, opts, args):
        if opts.xsdl is None:
            if len(args):
                opts.xsdl = args.pop(0)
            else:
                opts.xsdl = "-"
        return True
    
    def execute(self):
        Command_reserve.execute(self)

    def get_ticket(self):
        return self.ticket

    def madeReservation(self, ticket, task):
        self.ticket = ticket
        self.task = task
        Command_confirm.execute(self)
CommandFactory.getInstance().registerCommand(Command_submit, "submit", "sub", "s")

class Command_status(RemoteCommand, HasTicket):
    """\
    status: Request status information

    """

    def __init__(self, argv):
        """initialize the 'status' command."""
        RemoteCommand.__init__(self, argv)
        HasTicket.__init__(self, self.parser)

    def check_opts_and_args(self, opts, args):
        if opts.ticket is None:
            if len(args):
                opts.ticket = args.pop(0)
            else:
                raise CommandFailed("ticket required")
        return True
    
    def execute(self):
        ticket = self.get_ticket()
        self.scheduleTimeout(name="status-request")
        self.requestStatus(ticket)

    def statusListReceived(self, statusList):
        self.cancelTimeout()
        print repr(statusList)
        self.done()
CommandFactory.getInstance().registerCommand(Command_status, "status", "st")

class Command_showcache(RemoteCommand):
    """\
    showcache (sc): show cache entries

    """

    def __init__(self, argv):
        """initialize the 'status' command."""
        RemoteCommand.__init__(self, argv)

    def execute(self):
        self.scheduleTimeout(name="show-cache")
        self.requestCacheList()

    def cacheEntriesReceived(self, cache_entries):
        self.cancelTimeout()
        print repr(cache_entries)
        self.done()
CommandFactory.getInstance().registerCommand(Command_showcache, "showcache", "sc")

class CommandLineClient:
    def __init__(self):
        pass

    def setup_logging(self, verbose=False):
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
                    prot, host, stomp_queue, u1, u2, u3 = network.urlparse(cmd.opts.server)
                    if prot != "stomp":
                        raise ValueError("I do not understand this wire-protocol", prot)
                    
                    from xbe.cmdline.protocol import ClientProtocolFactory, ClientXMLProtocol
                    # TODO: generate ID or use some given one
                    factory = ClientProtocolFactory(
                        id=str(uuid.uuid4()),
                        stomp_user="test-user-1", stomp_pass="test-pass-1",
                        certificate=cmd.user_cert, ca_cert=cmd.ca_cert,
                        server_queue=stomp_queue,
                        protocolFactory=ClientXMLProtocol,
                        protocolFactoryArgs=(cmd,))
                    
                    from twisted.internet import reactor
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
                                                (sys.argv[0],s) for s in str(cf.message).split('\n')])
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

"""A class that can be used to create daemon processes."""

from optparse import OptionParser
import os, sys, signal, errno, time
import pwd, grp

SUCCESS = 0
FAILURE = 1

if hasattr(os, "devnull"):
    REDIRECT_TO = os.devnull
else:
    REDIRECT_TO = "/dev/null"

class Daemon(object):
    MAXFD = 1024
    def __init__(self, pidfile, daemonize=True, workdir="/", umask=0, user="nobody", group="nogroup"):
        self.pidfile = pidfile
        self.daemonize=daemonize
        self.workdir = workdir
        self.umask = umask
        self.user = user
        self.group = group
        self.parser = OptionParser()
        self.setFunction(self.run)

    def handle_request(self, req_type):
        try:
            req = getattr(self, "do_%s" % req_type)
        except AttributeError:
            self.error("usage: " + sys.argv[0] + " [options] start|stop|restart")
        req()

    def setFunction(self, f, *args, **kw):
        self.__daemon, self.__daemonArgs, self.__daemonKwords = (f, args, kw)

    def status(self):
        """I check my current status.

        return a tupel consisting of (pid, True) if running (-1, False) otherwise
        """
        try:
            pid = self.getpid()
            os.kill(pid, signal.SIG_DFL)
            return pid, True
        except OSError, e:
            if e.errno == errno.ESRCH:
                return pid, False
            else:
                raise Exception, "%s [%d]" % (e.strerror, e.errno)
        except IOError, e:
            raise Exception, "%s: %s" % (e.strerror, e.filename)
            
    def getpid(self):
        return int(open(self.pidfile).read())

    def error(self, msg, exitcode=FAILURE):
        """I print the message and exit with exitcode."""
        print >>sys.stderr, msg
        sys.exit(exitcode)

    def success(self, msg = None):
        """I print message and exit with SUCCESS"""
        if not msg is None:
            print >>sys.stdout, msg
        sys.exit(SUCCESS)
    
    def do_stop(self):
        """I stop the process whose pid is stored in the file pointed to by self.pidfile."""
        try:
            pid, running = self.status()
        except Exception, e:
            self.error("unknown: %s" % e)
        
        try:
            os.kill(pid, signal.SIG_DFL)
        except OSError, oe:
            if oe.errno == errno.ESRCH:
                return

        # process still running, so try to terminate it
        trials = 3
        while trials:
            # send TERM signal
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError, oe:
                if oe.errno != errno.ESRCH:
                    self.error(oe.message)
            time.sleep(1)
            trials -= 1

        # process did not cooperate, so kill it
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError, oe:
            if oe.errno != errno.ESRCH:
                self.error(oe.message)

    def do_status(self):
        try:
            pid, running = self.status()
            if pid >= 0 and running:
                self.success("alive with pid %d" % pid)
        except Exception, e:
            self.error("unknown: %s" % e)
        else:
            self.error("dead")

    def __check_parameters(self):
        """checks and sanitizes some parameters.

        * user and groups may be given as "names" or "ids",
          this function handles both cases.
        """
        
        # check the uids
        try:
            if isinstance(self.user, basestring):
                uid = pwd.getpwnam(self.user).pw_uid
            else:
                uid = pwd.getpwuid(self.user).pw_uid
        except KeyError, e:
            raise Exception("no such user: '%s'" % (str(self.user)))
        try:
            if isinstance(self.group, basestring):
                gid = grp.getgrnam(self.group).gr_gid
            else:
                gid = grp.getgrgid(self.group).gr_gid
        except KeyError, e:
            raise Exception("no such group: '%s'" % (str(self.user)))
        self.runas = ((uid, self.user), (gid, self.group))

    def do_restart(self):
        """Restart the daemon."""
        self.handle_request("stop")
        self.handle_request("start")

    def do_start(self):
        """Start the daemon.

        * checks if a process for the given pidfile is still running and fails accordingly
        """
        # check if one is running
        try:
            pid, running = self.status()
            if pid >= 0 and running:
                self.error("process already running with pid %d" % pid)
        except Exception, e:
            pass

        try:
            self.__check_parameters()
        except Exception, e:
            self.error(e)
            
        
        if self.daemonize:
            self._daemonize()
        self.__startup()
        self.__run()

    def _daemonize(self):
        """Daemonizes the current process.

        Forks several times to disconnect from parent and terminal and
        makes itself a session leader.

        the code is slightly adopted from that found on:
           http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/278731
        """
        # Fork a child  process so the parent can  exit.  This returns
        # control to  the command-line  or shell.  It  also guarantees
        # that the child will not be a process group leader, since the
        # child receives  a new process  ID and inherits  the parent's
        # process group ID.  This step  is required to insure that the
        # next call to os.setsid is successful.
        try:
            pid = os.fork()
        except OSError, oe:
            self.error("%s [%d]" % (oe.strerror, oe.errno))
        if pid != 0:
            # the father may exit
            os._exit(0)

        # To become  the session  leader of this  new session  and the
        # process  group leader  of  the new  process  group, we  call
        # os.setsid().  The  process is also guaranteed not  to have a
        # controlling terminal.  the first child becomes a new session
        # leader
        os.setsid()

        # Is ignoring SIGHUP necessary?
        #
        # It's  often  suggested  that  the SIGHUP  signal  should  be
        # ignored   before  the   second  fork   to   avoid  premature
        # termination  of the process.   The reason  is that  when the
        # first  child  terminates, all  processes,  e.g.  the  second
        # child, in the orphaned group will be sent a SIGHUP.
        #
        # "However, as  part of  the session management  system, there
        # are exactly two cases where SIGHUP is sent on the death of a
        # process:
        #
        # 1) When the  process that  dies is the  session leader  of a
        #      session that  is attached to a  terminal device, SIGHUP
        #      is  sent to  all  processes in  the foreground  process
        #      group of that terminal device.
        # 2) When the  death of  a process causes  a process  group to
        #      become  orphaned,  and one  or  more  processes in  the
        #      orphaned group are stopped, then SIGHUP and SIGCONT are
        #      sent to all members of the orphaned group." [2]
        #
        # The first case can be  ignored since the child is guaranteed
        # not to  have a controlling terminal.  The  second case isn't
        # so easy to dismiss.  The  process group is orphaned when the
        # first  child  terminates  and  POSIX.1 requires  that  every
        # STOPPED  process in  an  orphaned process  group  be sent  a
        # SIGHUP  signal  followed by  a  SIGCONT  signal.  Since  the
        # second  child is not  STOPPED though,  we can  safely forego
        # ignoring  the SIGHUP  signal.   In any  case,  there are  no
        # ill-effects if it is ignored.
        #
        # import signal           # Set handlers for asynchronous events.
        # signal.signal(signal.SIGHUP, signal.SIG_IGN)

        try:
            # Fork  a second  child  and exit  immediately to  prevent
            # zombies.   This causes  the second  child process  to be
            # orphaned,  making the init  process responsible  for its
            # cleanup.  And, since the first child is a session leader
            # without a controlling terminal,  it's possible for it to
            # acquire one by opening  a terminal in the future (System
            # V- based systems).  This second fork guarantees that the
            # child  is no  longer  a session  leader, preventing  the
            # daemon from ever acquiring a controlling terminal.
            pid = os.fork()# Fork a second child.
        except OSError, e:
            raise Exception, "%s [%d]" % (e.strerror, e.errno)

        if pid != 0:
            os._exit(0)
            
    def __startup(self):
        """common code for both cases, daemonize or not.

        essentially it does the following:
            * change to the working directory
            * set the umask
            * close all filedescriptors
            * redirect stdin,stdout,stderr to /dev/null
        """
        # change to working directory
        os.chdir(self.workdir)
        # set a new umask
        os.umask(self.umask)

        self._setup_priviledged()
        self.drop_priviledges()
        self._setup_unpriviledged()

        # Resource usage information.
        import resource
        maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
        if (maxfd == resource.RLIM_INFINITY):
            maxfd = Daemon.MAXFD
        # Iterate through and close all file descriptors.
        for fd in range(0, maxfd):
            try:
                os.close(fd)
            except OSError:# ERROR, fd wasn't open to begin with (ignored)
                pass
            
        # Redirect the standard I/O  file descriptors to the specified
        # file.  Since  the daemon  has no controlling  terminal, most
        # daemons  redirect stdin,  stdout, and  stderr  to /dev/null.
        # This is  done to prevent side-effects from  reads and writes
        # to the standard I/O file descriptors.
        
        # This call  to open is  guaranteed to return the  lowest file
        # descriptor,  which will be  0 (stdin),  since it  was closed
        # above.
        os.open(REDIRECT_TO, os.O_RDWR) # standard input (0)
        
        # Duplicate standard input to standard output and standard error.
        os.dup2(0, 1)  # standard output (1)
        os.dup2(0, 2)  # standard error (2)

    def __run(self):
        self.__daemon(self.__daemonArgs, self.__daemonKwords)

    def write_pid(self):
        """this method is called before dropping priviledges"""
        open(self.pidfile, "w").write(str(os.getpid()))

    def setup_logging(self):
        """initialize what is needed to have logging available."""
        pass
        
    def drop_priviledges(self):
        os.setgid(self.runas[1][0])
        os.setuid(self.runas[0][0])

    def _setup_priviledged(self):
        self.setup_logging()
        self.write_pid()

        # user specified stuff
        self.setup_priviledged()

    def _setup_unpriviledged(self):

        # user specified stuff
        self.setup_unpriviledged()

    # handler methods, that one can override in a subclass
    def setup_priviledged(self):
        """Called when we are about to setup ourself but have not dropped our priviledges yet."""
        pass

    def setup_unpriviledged(self):
        """Priviledges have been dropped."""
        pass

    def run(self, *args, **kw):
        """The default function run by the daemon.

        Override it or specify one with setFunction()
        """
        raise RuntimeError("either specify a function to run with 'setFunction()' or override this method!")

def f(*args, **kw):
    out = open ("/tmp/test-out", "wb")
    for i in xrange(60):
        print >>out, i
        out.flush()
        time.sleep(1)

if __name__ == "__main__":
    d = Daemon("/tmp/foobar", daemonize=True, user="nobody", group="nogroup")
    d.setFunction(f, "foo", "bar")
    d.handle_request(sys.argv[1])

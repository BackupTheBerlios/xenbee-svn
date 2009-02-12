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

"""The protocol spoken between the xbed and the instance-daemon."""

import logging, os, os.path, sys, time
log = logging.getLogger(__name__)

from twisted.internet import reactor, task

from xbe.util.network import discover_ips
from xbe.stomp.proto import StompTransport
from xbe.proto import XenBEEProtocolFactory, XenBEEProtocol
from xbe.xbeinstd.protocol.process import XBEProcessProtocol
from xbe.xbeinstd.daemon import XBEInstDaemon
from xbe.xml import message, errcode, protocol as xmlprotocol, jsdl
from xbe.xml.namespaces import *

class XBEInstProtocol(xmlprotocol.XMLProtocol):
    def __init__(self):
        xmlprotocol.XMLProtocol.__init__(self)
        self.aliveSender = task.LoopingCall(self.sendAliveMessage)

    def connectionMade(self):
        # send instance available message
        log.info("notifying xbe daemon, that i am available now")
        try:
            msg = message.InstanceAvailable(self.factory.instance_id)
            try:
                stompServer = (XBEInstDaemon.getInstance().host,
                               XBEInstDaemon.getInstance().port)
                
                # discover our ips and add to the message
                map(msg.add_ip, discover_ips(stompServer))
            except Exception, e:
                log.error("could not discover my ip: %s", e)
            self.sendMessage(self.transformResultToMessage(msg))
        except Exception, e:
            log.exception("send failed: %s" % e)
            raise

        # send an alive packet every 30 seconds
        self.aliveSender.start(30, now=False)

        # register signal handler, so that we can send a final message
        import signal
        signal.signal(signal.SIGTERM, self.sig_TERM)
        signal.signal(signal.SIGINT, self.sig_TERM)

    def sig_TERM(self, signal, stack_frame):
        self.aliveSender.stop()
        self.sendMessage(
            self.transformResultToMessage(
            message.InstanceShuttingDown(self.factory.instance_id, signal)))
        log.info("sent shutdown notification")
        reactor.callLater(1, reactor.stop)

    def __get_uptime(self):
        if os.path.exists("/proc/uptime"):
            return map(float, open("/proc/uptime").read().split())
        return (None, None)

    def sendAliveMessage(self):
        _id = self.factory.instance_id
        _uptime, _idle = self.__get_uptime()
        msg = message.InstanceAlive(_id, _uptime, _idle)
        self.sendMessage(self.transformResultToMessage(msg))

    def do_ExecuteTask(self, xml, *a, **kw):
        msg = message.MessageBuilder.from_xml(xml.getroottree())
        self.task_id = msg.task_id()
        return self.do_JobDefinition(msg.jsdl())

    def do_TerminateTask(self, xml, *a, **kw):
        msg = message.MessageBuilder.from_xml(xml.getroottree())
        if msg.task_id() != self.task_id():
            return message.Error(errcode.ILLEGAL_REQUEST, "task-id does not match")

        try:
            p = self.proc
        except AttributeError:
            pass
        else:
            p.process.signalProcess("KILL")
        self.sig_TERM(signal.SIGTERM, None)
        
    def do_JobDefinition(self, job_def, *a, **kw):
        try:
            self.proc
        except AttributeError:
            pass
        else:
            # there is already a job running right now
            return message.Error(errcode.JOB_ALREADY_RUNNING)

        xbeinstd = XBEInstDaemon.getInstance()
        jsdl_doc = jsdl.JsdlDocument(schema_map=xbeinstd.schema_map)
        parsed_jsdl = jsdl_doc.parse(job_def)

        try:
            app = jsdl_doc.lookup_path(
                "JobDefinition/JobDescription/Application"
            )
        except Exception, e:
            log.fatal("no application found")
            return message.Error(errcode.NO_APPLICATION)

        known_filesystems = jsdl_doc.get_file_systems()
        def __resolve(name, known_fs):
            rel_part = name[0]
            fs_name = name[1]
            if fs_name is not None:
                rel_part = rel_part.lstrip("/")
                return os.path.join(known_fs[fs_name], rel_part)
            else:
                return rel_part

        if app.get("POSIXApplication") is not None:
            # start a posix application
            posix_app = app.get("POSIXApplication")

            # build argv
            executable = __resolve(posix_app["Executable"],
                                   known_filesystems)
            args = posix_app.get("Argument")
            if args is not None:
                args = map(lambda a: __resolve(a, known_filesystems),
                           args)
            else:
                args = []
            argv = [executable]
            argv.extend(args)

            # working directory
            wd = posix_app.get("WorkingDirectory")
            if wd is not None:
                wd = __resolve(wd, known_filesystems)
            else:
                wd = "/"
            
            # build environment
            env = posix_app.get("Environment")
            environ = { "MQS": "%s://%s:%d" % (xbeinstd.proto, xbeinstd.host, xbeinstd.port) }
            if env is not None:
                for key, val, fs in env:
                    environ[key] = __resolve((val,fs), known_filesystems)
                
            # input, output, error
            input_file = posix_app.get("Input")
            if input_file is not None:
                input_file = __resolve(input_file, known_filesystems)
            else:
                input_file = "/dev/null"
            output_file = posix_app.get("Output")
            if output_file is not None:
                output_file = __resolve(output_file, known_filesystems)
            else:
                output_file = "/dev/null"
            error_file = posix_app.get("Error")
            if error_file is not None:
                error_file = __resolve(error_file, known_filesystems)
            else:
                error_file = "/dev/null"

            try:
                log.info("executing task: " + `argv`)
                child_streams = (
                    open(input_file, 'rb'),
                    open(output_file, 'wb'),
                    open(error_file, 'wb')
                )

                self.proc = XBEProcessProtocol(self)
                self.proc.cmdline = argv
                self.proc.process = reactor.spawnProcess(self.proc, argv[0], argv, env=environ,
                                                         path=wd, childFDs={
                    0: child_streams[0].fileno(),
                    1: child_streams[1].fileno(),
                    2: child_streams[2].fileno()
                    }
                )
            except Exception, e:
                log.warn("could not spawn process")
                if hasattr(self, "proc"):
                    del self.proc
                return message.Error(errcode.EXECUTION_FAILED, str(e))
        elif app.get("XBEApplication") is not None:
            xbe_app = app.get("XBEApplication")
            if xbe_app.get("ContinuousTask") is not None:
                log.info("executing continuous task to keep instance alive...")
            else:
                return message.Error(errcode.NO_APPLICATION,
                                     "illegal application element")
        else:
            return message.Error(errcode.NO_APPLICATION,
                                 "illegal application element")
            
            
    # process handling callbacks
    def processEnded(self, status_object):
        log.info("process ended: code:%d" %
                 (status_object.value.exitCode))
	os.system("/bin/sync")
        msg = message.ExecutionFinished(
            inst_id=self.factory.instance_id,
            exitcode=status_object.value.exitCode)
        self.sendMessage(self.transformResultToMessage(msg))
        del self.proc

class XenBEEInstProtocolFactory(XenBEEProtocolFactory):
    def __init__(self, daemon, instance_id, my_queue, server_queue, username, password):
	XenBEEProtocolFactory.__init__(self, my_queue, username, password) # "instance-%s"%instance_id)
        self.instance_id = instance_id
        self.p = None
        self.server_queue = server_queue
        self.daemon = daemon

    def dispatchToProtocol(self, transport, msg, domain, sourceType, sourceId=None):
        self.p.messageReceived(msg)

    def stompConnectionMade(self, stomp_protocol):
        if self.p is None:
            self.p = XBEInstProtocol()
            self.p.factory = self
            self.p.makeConnection(xmlprotocol.XMLTransport(
                StompTransport(stomp_protocol, self.server_queue)))

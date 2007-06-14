#!/usr/bin/env python

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

"""Test cases for the TaskFSM."""

__version__ = "$Rev$"
__author__ = "$Author$"

import unittest
from xbe.util.fsm import FSMError, FSMException, NoTransition
from xbe.xbed.task_fsm import TaskFSM

class TestFSM(TaskFSM):
    def __init__(self):
        TaskFSM.__init__(self)
        self.called = None

    # FSM transitions
    def do_confirmed(self, *args, **kw):
        self.called = "do_confirmed"

    def do_terminate_pending_reserved(self, reason, *args, **kw):
        self.called = "do_terminate_pending_reserved"
        self.reason = reason

    def do_terminate_pending_confirmed(self, reason, *args, **kw):
        self.called = "do_terminate_pending_confirmed"
        self.reason = reason

    def do_stage_in(self, *args, **kw):
        # this method must be asynchronous
        # addCallback(self.stage_in_completed).addErrback(self.failed)
        # pre-cond: task description and non-file resources available
        # post-cond: state == Running:Stage-In
        self.called = "do_stage_in"

    def do_terminate_stage_in(self, reason, *args, **kw):
        # terminate the stage-in process, must not fail
        self.called = "do_terminate_stage_in"
        self.reason = reason

    def do_stage_in_failed(self, reason, *args, **kw):
        # handle the case, that the staging failed
        self.called = "do_stage_in_failed"
        self.reason = reason

    def do_start_instance(self, *args, **kw):
        # all files are staged in, so trigger the start of the instance
        # addCallback(self.instance_started).addErrback(self.failed)
        self.called = "do_start_instance"

    def do_terminate_instance_starting(self, reason, *args, **kw):
        self.called = "do_terminate_instance_starting"
        self.reason = reason

    def do_instance_starting_failed(self, reason, *args, **kw):
        # handle a failed instance start attempt
        self.called = "do_instance_starting_failed"
        self.reason = reason

    def do_execute_task(self, *args, **kw):
        # pre-cond. instance available
        # post-cond. jsdl sent to instance
        self.called = "do_execute_task"

    def do_terminate_execution(self, reason, *args, **kw):
        # terminate the execution within the instance
        self.called = "do_terminate_execution"
        self.reason = reason

    def do_execution_failed(self, reason, *args, **kw):
        # the task execution failed
        self.called = "do_execution_failed"
        self.reason = reason

    def do_stop_instance(self, *args, **kw):
        # stop the instance
        self.called = "do_stop_instance"

    def do_terminate_instance_stopping(self, reason, *args, **kw):
        # terminate the shutdown-process
        # I think that has to be a 'noop', but the 'instance-stopped' callback
        # must not do any harm!
        self.called = "do_terminate_instance_stopping"
        self.reason = reason

    def do_instance_stopping_failed(self, reason, *args, **kw):
        # i really do not know, what to do about that, maybe force the destroying
        self.called = "do_instance_stopping_failed"
        self.reason = reason

    def do_stage_out(self, *args, **kw):
        # task has finished its execution,
        # instance has been shut down, stage out the data
        self.called = "do_stage_out"

    def do_stage_out_failed(self, reason, *args, **kw):
        # stage out process failed, so handle that
        self.called = "do_stage_out_failed"
        self.reason = reason

    def do_terminate_stage_out(self, reason, *args, **kw):
        # user requested the termination of this task
        self.called = "do_terminate_stage_out"
        self.reason = reason

    def do_task_finished(self):
        # pre-cond: stage-out is complete
        self.called = "do_task_finished"


class TestTaskFSM(unittest.TestCase):
    def setUp(self):
        self.fsm = TestFSM()

    def test_initial_state(self):
        self.assertEqual(self.fsm.state(), "Pending:Reserved")
        self.assertEqual(self.fsm.called, None)

    def test_length_1_confirm(self):
        self.fsm.confirm()
        self.assertEqual(self.fsm.state(), "Pending:Confirmed")
        self.assertEqual(self.fsm.called, "do_confirmed")
    def test_length_1_terminate(self):
        self.fsm.terminate("just for fun")
        self.assertEqual(self.fsm.state(), "Terminated")
        self.assertEqual(self.fsm.reason, "just for fun")
        self.assertEqual(self.fsm.called, "do_terminate_pending_reserved")
    def test_length_1_fail(self):
        try:
            self.fsm.failed("should not work")
        except NoTransition:
            pass
        else:
            self.fail("NoTransition error expected")

    def test_length_2_confirm_terminate(self):
        self.fsm.confirm()
        self.fsm.terminate("just for fun")
        self.assertEqual(self.fsm.state(), "Terminated")
        self.assertEqual(self.fsm.reason, "just for fun")
        self.assertEqual(self.fsm.called, "do_terminate_pending_confirmed")
    def test_length_2_confirm_start(self):
        self.fsm.confirm()
        self.fsm.start()
        self.assertEqual(self.fsm.state(), "Running:Stage-In")
        self.assertEqual(self.fsm.called, "do_stage_in")

    def test_length_3_confirm_start_terminate(self):
        self.fsm.confirm()
        self.fsm.start()
        self.fsm.terminate("just for fun")
        self.assertEqual(self.fsm.state(), "Terminated")
        self.assertEqual(self.fsm.called, "do_terminate_stage_in")
    def test_length_3_confirm_start_failed(self):
        self.fsm.confirm()
        self.fsm.start()
        self.fsm.failed("just for fun")
        self.assertEqual(self.fsm.state(), "Failed")
        self.assertEqual(self.fsm.called, "do_stage_in_failed")
    def test_length_3_confirm_start_completed(self):
        self.fsm.confirm()
        self.fsm.start()
        self.fsm.cb_stage_in_completed()
        self.assertEqual(self.fsm.state(), "Running:Instance-Starting")
        self.assertEqual(self.fsm.called, "do_start_instance")

    def test_length_4_instance_failed(self):
        self.fsm.confirm()
        self.fsm.start()
        self.fsm.cb_stage_in_completed()
        self.fsm.failed("just for fun")
        self.assertEqual(self.fsm.state(), "Failed")
        self.assertEqual(self.fsm.called, "do_instance_starting_failed")
        self.assertEqual(self.fsm.reason, "just for fun")
    def test_length_4_instance_terminate(self):
        self.fsm.confirm()
        self.fsm.start()
        self.fsm.cb_stage_in_completed()
        self.fsm.terminate("just for fun")
        self.assertEqual(self.fsm.state(), "Terminated")
        self.assertEqual(self.fsm.called, "do_terminate_instance_starting")
        self.assertEqual(self.fsm.reason, "just for fun")
    def test_length_4_instance_started(self):
        self.fsm.confirm()
        self.fsm.start()
        self.fsm.cb_stage_in_completed()
        self.fsm.cb_instance_started()
        self.assertEqual(self.fsm.state(), "Running:Executing")
        self.assertEqual(self.fsm.called, "do_execute_task")

    def test_length_5_execute_failed(self):
        self.fsm.confirm()
        self.fsm.start()
        self.fsm.cb_stage_in_completed()
        self.fsm.cb_instance_started()
        self.fsm.failed("just for fun")
        self.assertEqual(self.fsm.state(), "Failed")
        self.assertEqual(self.fsm.called, "do_execution_failed")
        self.assertEqual(self.fsm.reason, "just for fun")
    def test_length_5_execution_terminate(self):
        self.fsm.confirm()
        self.fsm.start()
        self.fsm.cb_stage_in_completed()
        self.fsm.cb_instance_started()
        self.fsm.terminate("just for fun")
        self.assertEqual(self.fsm.state(), "Terminated")
        self.assertEqual(self.fsm.called, "do_terminate_execution")
        self.assertEqual(self.fsm.reason, "just for fun")
    def test_length_5_execution_done(self):
        self.fsm.confirm()
        self.fsm.start()
        self.fsm.cb_stage_in_completed()
        self.fsm.cb_instance_started()
        self.fsm.cb_execution_finished()
        self.assertEqual(self.fsm.state(), "Running:Instance-Stopping")
        self.assertEqual(self.fsm.called, "do_stop_instance")

    def test_length_6_instance_stopping_failed(self):
        self.fsm.confirm()
        self.fsm.start()
        self.fsm.cb_stage_in_completed()
        self.fsm.cb_instance_started()
        self.fsm.cb_execution_finished()
        self.fsm.failed("just for fun")
        self.assertEqual(self.fsm.state(), "Failed")
        self.assertEqual(self.fsm.called, "do_instance_stopping_failed")
        self.assertEqual(self.fsm.reason, "just for fun")
    def test_length_6_instance_stopping_terminate(self):
        self.fsm.confirm()
        self.fsm.start()
        self.fsm.cb_stage_in_completed()
        self.fsm.cb_instance_started()
        self.fsm.cb_execution_finished()
        self.fsm.terminate("just for fun")
        self.assertEqual(self.fsm.state(), "Terminated")
        self.assertEqual(self.fsm.called, "do_terminate_instance_stopping")
        self.assertEqual(self.fsm.reason, "just for fun")
    def test_length_6_instance_stopped(self):
        self.fsm.confirm()
        self.fsm.start()
        self.fsm.cb_stage_in_completed()
        self.fsm.cb_instance_started()
        self.fsm.cb_execution_finished()
        self.fsm.cb_instance_stopped()
        self.assertEqual(self.fsm.state(), "Running:Stage-Out")
        self.assertEqual(self.fsm.called, "do_stage_out")

    def test_length_7_stage_out_failed(self):
        self.fsm.confirm()
        self.fsm.start()
        self.fsm.cb_stage_in_completed()
        self.fsm.cb_instance_started()
        self.fsm.cb_execution_finished()
        self.fsm.cb_instance_stopped()
        self.fsm.failed("just for fun")
        self.assertEqual(self.fsm.state(), "Failed")
        self.assertEqual(self.fsm.called, "do_stage_out_failed")
        self.assertEqual(self.fsm.reason, "just for fun")
    def test_length_7_stage_out_terminate(self):
        self.fsm.confirm()
        self.fsm.start()
        self.fsm.cb_stage_in_completed()
        self.fsm.cb_instance_started()
        self.fsm.cb_execution_finished()
        self.fsm.cb_instance_stopped()
        self.fsm.terminate("just for fun")
        self.assertEqual(self.fsm.state(), "Terminated")
        self.assertEqual(self.fsm.called, "do_terminate_stage_out")
        self.assertEqual(self.fsm.reason, "just for fun")
    def test_length_7_stage_out_completed(self):
        self.fsm.confirm()
        self.fsm.start()
        self.fsm.cb_stage_in_completed()
        self.fsm.cb_instance_started()
        self.fsm.cb_execution_finished()
        self.fsm.cb_instance_stopped()
        self.fsm.cb_stage_out_completed()
        self.assertEqual(self.fsm.state(), "Finished")
        self.assertEqual(self.fsm.called, "do_task_finished")

def suite():
    s1 = unittest.makeSuite(TestTaskFSM, "test")
    return unittest.TestSuite((s1,))

if __name__ == "__main__":
    unittest.main()

"""A module, that simply contains the Finite State Machine of a task."""

from xbe.util import fsm

class TaskFSM(object):
    def __init__(self):
        """Initialize a new task fsm.

        Have a look at the source code for a pictogram of the state machine.
        """
        m = fsm.FSM()
        m.newState("Failed")                      # the task failed
        m.newState("Terminated")                  # the task has been terminated by the user
        m.newState("Pending:Reserved")            # initial state
        m.newState("Pending:Confirmed")           # the task has been confirmed by the user
        m.newState("Running:Stage-In")            # the task is 'running' and stages its files
        m.newState("Running:Instance-Starting")   # staging complete, instance is starting up
        m.newState("Running:Executing")           # the task is really executing
        m.newState("Running:Instance-Stopping")   # instance is currently being shutdown
        m.newState("Running:Stage-Out")           # task has ended and files are beeing staged out
        m.newState("Finished")                    # the task is completely finished

        #
        #
        #
        # *----------* confirm  +-----------+
        # | Pending  |--------->| Pending   |----->...
        # | Reserved |          | Confirmed |
        # *----------*          +-----------+
        #       \                 /
        #        \               /
        #         +-------------+
        #         | Terminated  |
        #         +-------------+
        m.setStartState("Pending:Reserved")
        m.addTransition("Pending:Reserved",    # src
                        "Pending:Confirmed",   # dst
                        "confirm_token", self.do_confirmed) # trigger and transition function
        m.addTransition("Pending:Reserved",
                        "Terminated",
                        "terminate_token", self.do_terminate_pending_reserved)
        m.addTransition("Pending:Confirmed",
                        "Terminated",
                        "terminate_token", self.do_terminate_pending_confirmed)
        m.addTransition("Pending:Confirmed",
                        "Running:Stage-In",
                        "start_token", self.do_stage_in)
#
#                                 +----------+
#                +--------------->|  Failed  |<--------------+-------------------+
#                |                +----------+               |                   |
#                |stage in            ^ inst                 | exec              |stage out
#                | failed             |failed                |failed             | failed
#                |                    |                      |                   |
#  start  +------+---+ stagein +------+-------+ instance +---+-----+ exec    +---+-----+
# ------->|  Running |-------->|   Running    |--------->| Running |-------->|Running  |--->..
#         | Stage-In |completed|inst starting | started  |Executing|finished |Stage-Out|
#         +------+---+         +------+-------+          +----+----+         +----+----+
#                |                    |                       |                   |
#                |                    v                       |                   |
#                |             +-------------+                |                   |
#                `------------>| Terminated  |<---------------+-------------------+
#                              +-------------+

        m.addTransition("Running:Stage-In",
                        "Terminated",
                        "terminate_token", self.do_terminate_stage_in)
        m.addTransition("Running:Stage-In",
                        "Failed",
                        "fail_token", self.do_stage_in_failed)
        m.addTransition("Running:Stage-In",
                        "Running:Instance-Starting",
                        "stage_in_completed_token", self.do_start_instance)
        m.addTransition("Running:Instance-Starting",
                        "Terminated",
                        "terminate_token", self.do_terminate_instance_starting)
        m.addTransition("Running:Instance-Starting",
                        "Failed",
                        "fail_token", self.do_instance_starting_failed)
        m.addTransition("Running:Instance-Starting",
                        "Running:Executing",
                        "instance_started_token", self.do_execute_task)
        m.addTransition("Running:Executing",
                        "Terminated",
                        "terminate_token", self.do_terminate_execution)
        m.addTransition("Running:Executing",
                        "Failed",
                        "fail_token", self.do_execution_failed)
        m.addTransition("Running:Executing",
                        "Running:Stage-Out",
                        "execution_finished_token", self.do_stage_out)
        m.addTransition("Running:Stage-Out",
                        "Failed",
                        "fail_token", self.do_stage_out_failed)
        m.addTransition("Running:Stage-Out",
                        "Terminated",
                        "terminate_token", self.do_terminate_stage_out)
        #
        # +-----------+ stageout +-----------+
        # |  Running  |--------->|  Finished |
        # | Stage-Out | complete |           |
        # +-----------+          +-----------+
        #
        #
        m.addTransition("Running:Stage-Out",
                        "Finished",
                        "stage_out_completed_token", self.do_task_finished)

        # no-op transitions
        m.addTransition("Terminated",
                        "Terminated",
                        "terminate_token", None)
        m.addTransition("Failed",
                        "Failed",
                        "terminate_token", None)
        m.addTransition("Failed",
                        "Failed",
                        "fail_token", None)
        self.fsm = m

    def state(self):
        """get the current state of the task."""
        return self.fsm.getCurrentState()

    # 'external' transition trigger  methods
    # those are triggers called from another source, such as a network
    # protocol stack
    def terminate(self, reason=None):
        """user requests the termination."""
        return self.fsm.consume("terminate_token", reason)

    def confirm(self, *args, **kw):
        """user confirmed the task"""
        self.fsm.consume("confirm_token", *args, **kw)
    def start(self, *args, **kw):
        """initiate the starting of the task."""
        self.fsm.consume("start_token", *args, **kw)

    # the  only errback to  be used,  it will  be transformed  into an
    # appropriate errback using the fsm
    def failed(self, reason):
        """The task has failed, reason should be a twisted.python.failure.Failure.

        An appropriate method that depends on the current state will be called.
        """
        self.fsm.consume("fail_token", reason)

    # callbacks, that will trigger FSM transitions
    # you can use them to trigger state changes
    def cb_stage_in_completed(self, *args, **kw):
        self.fsm.consume("stage_in_completed_token", *args, **kw)
    def cb_instance_started(self, *args, **kw):
        self.fsm.consume("instance_started_token", *args, **kw)
    def cb_execution_finished(self, *args, **kw):
        self.fsm.consume("execution_finished_token", *args, **kw)
    def cb_instance_stopped(self, *args, **kw):
        self.fsm.consume("instance_stopped_token", *args, **kw)
    def cb_stage_out_completed(self, *args, **kw):
        self.fsm.consume("stage_out_completed_token", *args, **kw)
        
    # FSM transitions override these in a subclass to add functionality
    def do_confirmed(self, *args, **kw):
        """The task has been confirmed by the user."""
        pass

    def do_terminate_pending_reserved(self, reason, *args, **kw):
        """terminate a pending task, that has not been confirmed yet.

        That should not impose much work to do.
        """
        pass

    def do_terminate_pending_confirmed(self, reason, *args, **kw):
        """terminate a confirmed task."""
        pass

    def do_stage_in(self, *args, **kw):
        """stage in all necessary files and wait for other resources.

        this method must be asynchronous
        addCallback(self.stage_in_completed).addErrback(self.failed)

        pre-cond: task description available and task has been confirmed
        post-cond: state == Running:Stage-In
        """
        pass

    def do_terminate_stage_in(self, reason, *args, **kw):
        """terminate the stage-in process, must not fail."""
        pass

    def do_stage_in_failed(self, reason, *args, **kw):
        """handle the case, that the staging failed"""
        pass

    def do_start_instance(self, *args, **kw):
        """all files are staged in, so trigger the start of the instance
           addCallback(self.cb_instance_started).addErrback(self.failed)"""
        pass

    def do_terminate_instance_starting(self, reason, *args, **kw):
        """terminate the start process of the instance."""
        pass

    def do_instance_starting_failed(self, reason, *args, **kw):
        """handle a failed instance start attempt"""
        pass

    def do_execute_task(self, *args, **kw):
        """execute the task
        pre-cond. instance available -> protocol is ready
        post-cond. jsdl sent to instance
        """
        pass

    def do_terminate_execution(self, reason, *args, **kw):
        """terminate the execution within the instance.

        1. terminate the task within the instance
        2. shutdown the instance
        """
        pass

    def do_execution_failed(self, reason, *args, **kw):
        """the task execution failed

        that should be something like 'do_stop_instance' with different callbacks
        """
        pass

    def do_stop_instance(self, *args, **kw):
        """the task has finished its execution stop the instance"""
        pass

    def do_terminate_instance_stopping(self, reason, *args, **kw):
        """terminate the shutdown-process
        I think that has to be a 'noop', but the 'instance-stopped' callback
        must not do any harm!"""
        pass

    def do_instance_stopping_failed(self, reason, *args, **kw):
        """i really do not know, what to do about that, maybe force the destroying"""
        pass

    def do_stage_out(self, *args, **kw):
        """task has finished its execution,
           instance has been shut down, stage out the data"""
        pass

    def do_stage_out_failed(self, reason, *args, **kw):
        """stage out process failed, so handle that"""
        pass

    def do_terminate_stage_out(self, *args, **kw):
        """terminate the stage out process"""
        pass

    def do_task_finished(self):
        """pre-cond: stage-out is complete"""
        pass

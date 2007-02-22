"""A module, that simply contains the Finite State Machine of a task."""


from xbe.util import fsm

class TaskFSM(object):
    def __init__(self):
        """Initialize a new task fsm."""
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
                        "confirm_token", self.do_confirmed) # trigger
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
#
#
#                                 +----------+
#                +--------------->|  Failed  |<--------------+------------------+----------+
#                |                +----------+               |                  |          |
#                |stage in            ^ inst                 | exec             |          |stage out
#                | failed             |failed                |failed            |          | failed
#                |                    |                      |                  |          |
#  start  +------+---+ stagein +------+-------+ instance +---+-----+ exec    +-------+ +---+-----+
# ------->|  Running |-------->|   Running    |--------->| Running |-------->|Running|-|Running  |--->..
#         | Stage-In |completed|inst starting | started  |Executing|finished |  stop | |Stage-Out|
#         +------+---+         +------+-------+          +----+----+         |  inst | +----+----+
#                |                    |                       |              +-------+      |
#                |                    v                       |                             |
#                |             +-------------+                |                             |
#                `------------>| Terminated  |<---------------+-----------------------------+
#                              +-------------+
#
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
                        "Running:Instance-Stopping",
                        "execution_finished_token", self.do_stop_instance)
        m.addTransition("Running:Instance-Stopping",
                        "Terminated",
                        "terminate_token", self.do_terminate_instance_stopping)
        m.addTransition("Running:Instance-Stopping",
                        "Failed",
                        "fail_token", self.do_instance_stopping_failed)
        m.addTransition("Running:Instance-Stopping",
                        "Running:Stage-Out",
                        "instance_stopped_token", self.do_stage_out)
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
        self.fsm = m

    def state(self):
        """get the current state of the task."""
        return self.fsm.getCurrentState()

    # 'external' transition trigger  methods
    # those are triggers called from another source, such as a network
    # protocol stack
    def failed(self, reason):
        """the task has failed, reason should be a twisted.python.failure.Failure."""
        return self.fsm.consume("fail_token", reason)
    def terminate(self, reason=None):
        """user requests the termination."""
        return self.fsm.consume("terminate_token", reason)

    def confirm(self):
        """user confirmed the task"""
        self.fsm.consume("confirm_token")
    def start(self):
        """initiate the starting of the task."""
        self.fsm.consume("start_token")
    def execute(self):
        """triggers the execution of the task."""
        self.fsm.consume("execute_task_token")

    # callbacks, that will trigger FSM transitions
    # you can use these to trigger state changes
    def cb_stage_in_completed(self, *args, **kw):
        self.fsm.consume("stage_in_completed_token")
    def cb_instance_started(self, *args, **kw):
        self.fsm.consume("instance_started_token")
    def cb_execution_finished(self, *args, **kw):
        self.fsm.consume("execution_finished_token")
    def cb_instance_stopped(self, *args, **kw):
        self.fsm.consume("instance_stopped_token")
    def cb_stage_out_completed(self, *args, **kw):
        self.fsm.consume("stage_out_completed_token")
        
    # FSM transitions override these in a subclass to add functionality
    def do_confirmed(self, *args, **kw):
        pass

    def do_terminate_pending_reserved(self, reason, *args, **kw):
        pass

    def do_terminate_pending_confirmed(self, reason, *args, **kw):
        pass

    def do_stage_in(self, *args, **kw):
        # this method must be asynchronous
        # addCallback(self.stage_in_completed).addErrback(self.failed)
        # pre-cond: task description and non-file resources available
        # post-cond: state == Running:Stage-In
        pass

    def do_terminate_stage_in(self, reason, *args, **kw):
        # terminate the stage-in process, must not fail
        pass

    def do_stage_in_failed(self, reason, *args, **kw):
        # handle the case, that the staging failed
        pass

    def do_start_instance(self, *args, **kw):
        # all files are staged in, so trigger the start of the instance
        # addCallback(self.instance_started).addErrback(self.failed)
        pass

    def do_terminate_instance_starting(self, reason, *args, **kw):
        pass

    def do_instance_starting_failed(self, reason, *args, **kw):
        # handle a failed instance start attempt
        pass

    def do_execute_task(self, *args, **kw):
        # pre-cond. instance available
        # post-cond. jsdl sent to instance
        pass

    def do_terminate_execution(self, reason, *args, **kw):
        # terminate the execution within the instance
        pass

    def do_execution_failed(self, reason, *args, **kw):
        # the task execution failed
        pass

    def do_stop_instance(self, *args, **kw):
        # stop the instance
        pass

    def do_terminate_instance_stopping(self, reason, *args, **kw):
        # terminate the shutdown-process
        # I think that has to be a 'noop', but the 'instance-stopped' callback
        # must not do any harm!
        pass

    def do_instance_stopping_failed(self, reason, *args, **kw):
        # i really do not know, what to do about that, maybe force the destroying
        pass

    def do_stage_out(self, *args, **kw):
        # task has finished its execution,
        # instance has been shut down, stage out the data
        pass

    def do_stage_out_failed(self, reason, *args, **kw):
        # stage out process failed, so handle that
        pass

    def do_terminate_stage_out(self, *args, **kw):
        # user requested the termination of this task
        pass

    def do_task_finished(self):
        # pre-cond: stage-out is complete
        pass

"""This module holds all error codes that may be sent."""

OK = 200
ILLEGAL_REQUEST = 400
SUBMISSION_FAILURE = 401
JOB_ALREADY_RUNNING = 402
TASK_LOOKUP_FAILURE = 404
INSTANCE_LOOKUP_FAILURE = 405
SIGNAL_OUT_OF_RANGE = 450
SECURITY_ERROR = 460
UNAUTHORIZED = 461
SERVER_BUSY = 470
INTERNAL_SERVER_ERROR = 500

info = {
    OK: ( "OK", "everything ok", None ),
    ILLEGAL_REQUEST: ("ILLEGAL REQUEST",
                      "you sent me an illegal request", None),
    SUBMISSION_FAILURE: ("SUBMISSION FAILURE",
                         "you sent me an illegal request", None),
    JOB_ALREADY_RUNNING: ("JOB ALREADY RUNNING",
                         "a job is already running on this instance", None),
    TASK_LOOKUP_FAILURE: ("TASK_LOOKUP_FAILURE",
                          "the task-id you sent could not be mapped to a task", None),
    INSTANCE_LOOKUP_FAILURE: ("INSTANCE_LOOKUP_FAILURE",
                              "the task-id you sent could not be mapped to a task", None),
    SIGNAL_OUT_OF_RANGE: ("SIGNAL_OUT_OF_RANGE",
                          "the signal you have sent was out of range", None),
    SECURITY_ERROR: ("SECURITY_ERROR", "general security violation", None),
    UNAUTHORIZED: ("UNAUTHORIZED", "you are not authorized", None),
    SERVER_BUSY: ("SERVER_BUSY", "I cannot handle your request right now, try again later", None),
    INTERNAL_SERVER_ERROR: ("INTERNAL_SERVER_ERROR", "you sent me an illegal request", None)
}

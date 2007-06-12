"""This module holds all error codes that may be sent."""

OK = 200
SERVER_BUSY = 300

ILLEGAL_REQUEST = 400
SUBMISSION_FAILURE = 401
JOB_ALREADY_RUNNING = 402
NO_INSTANCE_DESCRIPTION = 403
TASK_LOOKUP_FAILURE = 404
INSTANCE_LOOKUP_FAILURE = 405
NO_APPLICATION = 406
EXECUTION_FAILED = 407
CACHING_FAILED = 408
SIGNAL_OUT_OF_RANGE = 450

INTERNAL_SERVER_ERROR = 500
TICKET_INVALID = 501
SECURITY_ERROR = 502
UNAUTHORIZED = 503
SIGNATURE_MISSMATCH = 504
DECYPHER_FAILED = 505

info = {
    OK: ( "OK", "everything ok", None ),
    ILLEGAL_REQUEST: ("ILLEGAL REQUEST",
                      "you sent me an illegal request", None),
    SUBMISSION_FAILURE: ("SUBMISSION FAILURE",
                         "you sent me an illegal request", None),
    JOB_ALREADY_RUNNING: ("JOB ALREADY RUNNING",
                         "a job is already running on this instance", None),
    NO_INSTANCE_DESCRIPTION: ("NO_INSTANCE_DESCRIPTION",
                              "no instance description found", None),
    TASK_LOOKUP_FAILURE: ("TASK_LOOKUP_FAILURE",
                          "the task-id you sent could not be mapped to a task", None),
    INSTANCE_LOOKUP_FAILURE: ("INSTANCE_LOOKUP_FAILURE",
                              "the task-id you sent could not be mapped to a task", None),
    SIGNAL_OUT_OF_RANGE: ("SIGNAL_OUT_OF_RANGE",
                          "the signal you have sent was out of range", None),
    SECURITY_ERROR: ("SECURITY_ERROR", "general security violation", None),
    UNAUTHORIZED: ("UNAUTHORIZED", "you are not authorized", None),
    SIGNATURE_MISSMATCH: ("SIGNATURE MISSMATCH", "the signature did not match the message", None),
    DECYPHER_FAILED: ("DECYPHER FAILED", "message could not be decrypted", None),
    
    SERVER_BUSY: ("SERVER_BUSY",
                  "I cannot handle your request right now, try again later", None),
    NO_APPLICATION: ("NO_APPLICATION",
                     "No application found", None),
    INTERNAL_SERVER_ERROR: ("INTERNAL_SERVER_ERROR",
                            "you sent me an illegal request", None),
    TICKET_INVALID: ("TICKET_INVALID", "no ticket specified, or illegal ticket", None),
    EXECUTION_FAILED: ("EXECUTION_FAILED", "execution of the task failed", None),
    CACHING_FAILED: ("CACHING_FAILED", "caching of your file failed", None),
}

#!/usr/bin/python2.4
# Generated by the protocol buffer compiler.  DO NOT EDIT!

from google.protobuf import descriptor
from google.protobuf import message
from google.protobuf import reflection
from google.protobuf import service
from google.protobuf import service_reflection
from google.protobuf import descriptor_pb2
_ERRORCODE = descriptor.EnumDescriptor(
  name='ErrorCode',
  full_name='xbe.messages.ErrorCode',
  filename='ErrorCode',
  values=[
    descriptor.EnumValueDescriptor(
      name='UNKNOWN_ERROR', index=0, number=0,
      options=None,
      type=None),
  ],
  options=None,
)


_EXECUTENAKREASON = descriptor.EnumDescriptor(
  name='ExecuteNakReason',
  full_name='xbe.messages.ExecuteNakReason',
  filename='ExecuteNakReason',
  values=[
    descriptor.EnumValueDescriptor(
      name='UNKNOWN_REASON', index=0, number=0,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='RESOURCE_BUSY', index=1, number=1,
      options=None,
      type=None),
  ],
  options=None,
)


_STATUSCODE = descriptor.EnumDescriptor(
  name='StatusCode',
  full_name='xbe.messages.StatusCode',
  filename='StatusCode',
  values=[
    descriptor.EnumValueDescriptor(
      name='IDLE', index=0, number=0,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='RUNNING', index=1, number=1,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='FINISHED', index=2, number=2,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='FAILED', index=3, number=3,
      options=None,
      type=None),
  ],
  options=None,
)


_FAILREASON = descriptor.EnumDescriptor(
  name='FailReason',
  full_name='xbe.messages.FailReason',
  filename='FailReason',
  values=[
    descriptor.EnumValueDescriptor(
      name='UNKNOWN', index=0, number=0,
      options=None,
      type=None),
  ],
  options=None,
)


UNKNOWN_ERROR = 0
UNKNOWN_REASON = 0
RESOURCE_BUSY = 1
IDLE = 0
RUNNING = 1
FINISHED = 2
FAILED = 3
UNKNOWN = 0



_XBEMESSAGE = descriptor.Descriptor(
  name='XbeMessage',
  full_name='xbe.messages.XbeMessage',
  filename='xbemsg.proto',
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='header', full_name='xbe.messages.XbeMessage.header', index=0,
      number=1, type=11, cpp_type=10, label=2,
      default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='error', full_name='xbe.messages.XbeMessage.error', index=1,
      number=2, type=11, cpp_type=10, label=1,
      default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='execute', full_name='xbe.messages.XbeMessage.execute', index=2,
      number=3, type=11, cpp_type=10, label=1,
      default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='execute_ack', full_name='xbe.messages.XbeMessage.execute_ack', index=3,
      number=4, type=11, cpp_type=10, label=1,
      default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='execute_nak', full_name='xbe.messages.XbeMessage.execute_nak', index=4,
      number=5, type=11, cpp_type=10, label=1,
      default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='status_req', full_name='xbe.messages.XbeMessage.status_req', index=5,
      number=6, type=11, cpp_type=10, label=1,
      default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='status', full_name='xbe.messages.XbeMessage.status', index=6,
      number=7, type=11, cpp_type=10, label=1,
      default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='finished', full_name='xbe.messages.XbeMessage.finished', index=7,
      number=8, type=11, cpp_type=10, label=1,
      default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='finished_ack', full_name='xbe.messages.XbeMessage.finished_ack', index=8,
      number=9, type=11, cpp_type=10, label=1,
      default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='failed', full_name='xbe.messages.XbeMessage.failed', index=9,
      number=10, type=11, cpp_type=10, label=1,
      default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='failed_ack', full_name='xbe.messages.XbeMessage.failed_ack', index=10,
      number=11, type=11, cpp_type=10, label=1,
      default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='shutdown', full_name='xbe.messages.XbeMessage.shutdown', index=11,
      number=12, type=11, cpp_type=10, label=1,
      default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='shutdown_ack', full_name='xbe.messages.XbeMessage.shutdown_ack', index=12,
      number=13, type=11, cpp_type=10, label=1,
      default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='terminate', full_name='xbe.messages.XbeMessage.terminate', index=13,
      number=14, type=11, cpp_type=10, label=1,
      default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='terminate_ack', full_name='xbe.messages.XbeMessage.terminate_ack', index=14,
      number=15, type=11, cpp_type=10, label=1,
      default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='life_sign', full_name='xbe.messages.XbeMessage.life_sign', index=15,
      number=16, type=11, cpp_type=10, label=1,
      default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],  # TODO(robinson): Implement.
  enum_types=[
  ],
  options=None)


_HEADER = descriptor.Descriptor(
  name='Header',
  full_name='xbe.messages.Header',
  filename='xbemsg.proto',
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='conversation_id', full_name='xbe.messages.Header.conversation_id', index=0,
      number=1, type=12, cpp_type=9, label=2,
      default_value="",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],  # TODO(robinson): Implement.
  enum_types=[
  ],
  options=None)


_ERROR = descriptor.Descriptor(
  name='Error',
  full_name='xbe.messages.Error',
  filename='xbemsg.proto',
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='code', full_name='xbe.messages.Error.code', index=0,
      number=1, type=14, cpp_type=8, label=2,
      default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='message', full_name='xbe.messages.Error.message', index=1,
      number=2, type=9, cpp_type=9, label=1,
      default_value=unicode("", "utf-8"),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],  # TODO(robinson): Implement.
  enum_types=[
  ],
  options=None)


_TASK_ENV = descriptor.Descriptor(
  name='Env',
  full_name='xbe.messages.Task.Env',
  filename='xbemsg.proto',
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='key', full_name='xbe.messages.Task.Env.key', index=0,
      number=1, type=9, cpp_type=9, label=2,
      default_value=unicode("", "utf-8"),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='val', full_name='xbe.messages.Task.Env.val', index=1,
      number=2, type=9, cpp_type=9, label=2,
      default_value=unicode("", "utf-8"),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],  # TODO(robinson): Implement.
  enum_types=[
  ],
  options=None)

_TASK = descriptor.Descriptor(
  name='Task',
  full_name='xbe.messages.Task',
  filename='xbemsg.proto',
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='executable', full_name='xbe.messages.Task.executable', index=0,
      number=1, type=9, cpp_type=9, label=2,
      default_value=unicode("", "utf-8"),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='argument', full_name='xbe.messages.Task.argument', index=1,
      number=2, type=9, cpp_type=9, label=3,
      default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='env', full_name='xbe.messages.Task.env', index=2,
      number=3, type=11, cpp_type=10, label=3,
      default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='stdin', full_name='xbe.messages.Task.stdin', index=3,
      number=6, type=9, cpp_type=9, label=1,
      default_value=unicode("", "utf-8"),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='stdout', full_name='xbe.messages.Task.stdout', index=4,
      number=7, type=9, cpp_type=9, label=1,
      default_value=unicode("", "utf-8"),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='stderr', full_name='xbe.messages.Task.stderr', index=5,
      number=8, type=9, cpp_type=9, label=1,
      default_value=unicode("", "utf-8"),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='wd', full_name='xbe.messages.Task.wd', index=6,
      number=9, type=9, cpp_type=9, label=1,
      default_value=unicode("/", "utf-8"),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],  # TODO(robinson): Implement.
  enum_types=[
  ],
  options=None)


_EXECUTE = descriptor.Descriptor(
  name='Execute',
  full_name='xbe.messages.Execute',
  filename='xbemsg.proto',
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='main_task', full_name='xbe.messages.Execute.main_task', index=0,
      number=1, type=11, cpp_type=10, label=1,
      default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='status_task', full_name='xbe.messages.Execute.status_task', index=1,
      number=2, type=11, cpp_type=10, label=1,
      default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],  # TODO(robinson): Implement.
  enum_types=[
  ],
  options=None)


_EXECUTEACK = descriptor.Descriptor(
  name='ExecuteAck',
  full_name='xbe.messages.ExecuteAck',
  filename='xbemsg.proto',
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='task', full_name='xbe.messages.ExecuteAck.task', index=0,
      number=1, type=5, cpp_type=1, label=1,
      default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],  # TODO(robinson): Implement.
  enum_types=[
  ],
  options=None)


_EXECUTENAK = descriptor.Descriptor(
  name='ExecuteNak',
  full_name='xbe.messages.ExecuteNak',
  filename='xbemsg.proto',
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='reason', full_name='xbe.messages.ExecuteNak.reason', index=0,
      number=1, type=14, cpp_type=8, label=2,
      default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='message', full_name='xbe.messages.ExecuteNak.message', index=1,
      number=2, type=9, cpp_type=9, label=1,
      default_value=unicode("", "utf-8"),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],  # TODO(robinson): Implement.
  enum_types=[
  ],
  options=None)


_STATUSREQ = descriptor.Descriptor(
  name='StatusReq',
  full_name='xbe.messages.StatusReq',
  filename='xbemsg.proto',
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='execute_status_task', full_name='xbe.messages.StatusReq.execute_status_task', index=0,
      number=1, type=8, cpp_type=7, label=1,
      default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],  # TODO(robinson): Implement.
  enum_types=[
  ],
  options=None)


_STATUS = descriptor.Descriptor(
  name='Status',
  full_name='xbe.messages.Status',
  filename='xbemsg.proto',
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='status', full_name='xbe.messages.Status.status', index=0,
      number=1, type=14, cpp_type=8, label=2,
      default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='status_task_exit_code', full_name='xbe.messages.Status.status_task_exit_code', index=1,
      number=2, type=5, cpp_type=1, label=1,
      default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='stdout', full_name='xbe.messages.Status.stdout', index=2,
      number=3, type=12, cpp_type=9, label=1,
      default_value="",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='stderr', full_name='xbe.messages.Status.stderr', index=3,
      number=4, type=12, cpp_type=9, label=1,
      default_value="",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],  # TODO(robinson): Implement.
  enum_types=[
  ],
  options=None)


_FINISHED = descriptor.Descriptor(
  name='Finished',
  full_name='xbe.messages.Finished',
  filename='xbemsg.proto',
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='exitcode', full_name='xbe.messages.Finished.exitcode', index=0,
      number=1, type=5, cpp_type=1, label=2,
      default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='task', full_name='xbe.messages.Finished.task', index=1,
      number=2, type=5, cpp_type=1, label=1,
      default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],  # TODO(robinson): Implement.
  enum_types=[
  ],
  options=None)


_FINISHEDACK = descriptor.Descriptor(
  name='FinishedAck',
  full_name='xbe.messages.FinishedAck',
  filename='xbemsg.proto',
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='task', full_name='xbe.messages.FinishedAck.task', index=0,
      number=1, type=5, cpp_type=1, label=1,
      default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],  # TODO(robinson): Implement.
  enum_types=[
  ],
  options=None)


_FAILED = descriptor.Descriptor(
  name='Failed',
  full_name='xbe.messages.Failed',
  filename='xbemsg.proto',
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='task', full_name='xbe.messages.Failed.task', index=0,
      number=1, type=5, cpp_type=1, label=1,
      default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='reason', full_name='xbe.messages.Failed.reason', index=1,
      number=2, type=14, cpp_type=8, label=1,
      default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],  # TODO(robinson): Implement.
  enum_types=[
  ],
  options=None)


_FAILEDACK = descriptor.Descriptor(
  name='FailedAck',
  full_name='xbe.messages.FailedAck',
  filename='xbemsg.proto',
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='task', full_name='xbe.messages.FailedAck.task', index=0,
      number=1, type=5, cpp_type=1, label=1,
      default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],  # TODO(robinson): Implement.
  enum_types=[
  ],
  options=None)


_SHUTDOWN = descriptor.Descriptor(
  name='Shutdown',
  full_name='xbe.messages.Shutdown',
  filename='xbemsg.proto',
  containing_type=None,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],  # TODO(robinson): Implement.
  enum_types=[
  ],
  options=None)


_SHUTDOWNACK = descriptor.Descriptor(
  name='ShutdownAck',
  full_name='xbe.messages.ShutdownAck',
  filename='xbemsg.proto',
  containing_type=None,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],  # TODO(robinson): Implement.
  enum_types=[
  ],
  options=None)


_TERMINATE = descriptor.Descriptor(
  name='Terminate',
  full_name='xbe.messages.Terminate',
  filename='xbemsg.proto',
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='task', full_name='xbe.messages.Terminate.task', index=0,
      number=1, type=5, cpp_type=1, label=1,
      default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],  # TODO(robinson): Implement.
  enum_types=[
  ],
  options=None)


_TERMINATEACK = descriptor.Descriptor(
  name='TerminateAck',
  full_name='xbe.messages.TerminateAck',
  filename='xbemsg.proto',
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='task', full_name='xbe.messages.TerminateAck.task', index=0,
      number=1, type=5, cpp_type=1, label=1,
      default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],  # TODO(robinson): Implement.
  enum_types=[
  ],
  options=None)


_LIFESIGN = descriptor.Descriptor(
  name='LifeSign',
  full_name='xbe.messages.LifeSign',
  filename='xbemsg.proto',
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='tstamp', full_name='xbe.messages.LifeSign.tstamp', index=0,
      number=1, type=4, cpp_type=4, label=2,
      default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='status', full_name='xbe.messages.LifeSign.status', index=1,
      number=2, type=14, cpp_type=8, label=1,
      default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],  # TODO(robinson): Implement.
  enum_types=[
  ],
  options=None)


_XBEMESSAGE.fields_by_name['header'].message_type = _HEADER
_XBEMESSAGE.fields_by_name['error'].message_type = _ERROR
_XBEMESSAGE.fields_by_name['execute'].message_type = _EXECUTE
_XBEMESSAGE.fields_by_name['execute_ack'].message_type = _EXECUTEACK
_XBEMESSAGE.fields_by_name['execute_nak'].message_type = _EXECUTENAK
_XBEMESSAGE.fields_by_name['status_req'].message_type = _STATUSREQ
_XBEMESSAGE.fields_by_name['status'].message_type = _STATUS
_XBEMESSAGE.fields_by_name['finished'].message_type = _FINISHED
_XBEMESSAGE.fields_by_name['finished_ack'].message_type = _FINISHEDACK
_XBEMESSAGE.fields_by_name['failed'].message_type = _FAILED
_XBEMESSAGE.fields_by_name['failed_ack'].message_type = _FAILEDACK
_XBEMESSAGE.fields_by_name['shutdown'].message_type = _SHUTDOWN
_XBEMESSAGE.fields_by_name['shutdown_ack'].message_type = _SHUTDOWNACK
_XBEMESSAGE.fields_by_name['terminate'].message_type = _TERMINATE
_XBEMESSAGE.fields_by_name['terminate_ack'].message_type = _TERMINATEACK
_XBEMESSAGE.fields_by_name['life_sign'].message_type = _LIFESIGN
_ERROR.fields_by_name['code'].enum_type = _ERRORCODE
_TASK.fields_by_name['env'].message_type = _TASK_ENV
_EXECUTE.fields_by_name['main_task'].message_type = _TASK
_EXECUTE.fields_by_name['status_task'].message_type = _TASK
_EXECUTENAK.fields_by_name['reason'].enum_type = _EXECUTENAKREASON
_STATUS.fields_by_name['status'].enum_type = _STATUSCODE
_FAILED.fields_by_name['reason'].enum_type = _FAILREASON
_LIFESIGN.fields_by_name['status'].enum_type = _STATUSCODE

class XbeMessage(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _XBEMESSAGE

class Header(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _HEADER

class Error(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _ERROR

class Task(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  
  class Env(message.Message):
    __metaclass__ = reflection.GeneratedProtocolMessageType
    DESCRIPTOR = _TASK_ENV
  DESCRIPTOR = _TASK

class Execute(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _EXECUTE

class ExecuteAck(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _EXECUTEACK

class ExecuteNak(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _EXECUTENAK

class StatusReq(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _STATUSREQ

class Status(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _STATUS

class Finished(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _FINISHED

class FinishedAck(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _FINISHEDACK

class Failed(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _FAILED

class FailedAck(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _FAILEDACK

class Shutdown(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _SHUTDOWN

class ShutdownAck(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _SHUTDOWNACK

class Terminate(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _TERMINATE

class TerminateAck(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _TERMINATEACK

class LifeSign(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _LIFESIGN


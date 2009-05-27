# Finds the zero mq library
#
# ZeroMQ is available from http://www.zeromq.org
#
# This file defines:
# * ZMQ_FOUND if the library and include files were found
# * ZMQ_SERVER if the server could be found it's location is set here - not required for building
# * ZMQ_LIBRARY the library used to link to zmq (static is preferred)
# * ZMQ_INCLUDE_DIR the inlude directory for the zmq header files

if(ZMQ_HOME MATCHES "")
  if("" MATCHES "$ENV{ZMQ_HOME}")
#    message(STATUS "ZMQ_HOME env is not set, setting it to /usr/local")
    set (ZMQ_HOME "/usr/local")
  else("" MATCHES "$ENV{ZMQ_HOME}")
    set (ZMQ_HOME "$ENV{ZMQ_HOME}")
  endif("" MATCHES "$ENV{ZMQ_HOME}")
else(ZMQ_HOME MATCHES "")
#  message(STATUS "ZMQ_HOME is not empty: \"${ZMQ_HOME}\"")
  set (ZMQ_HOME "${ZMQ_HOME}")
endif(ZMQ_HOME MATCHES "")

# find the include files
FIND_PATH(ZMQ_INCLUDE_DIR zmq/message.hpp
  ${ZMQ_HOME}/include
  ${CMAKE_INCLUDE_PATH}
  /usr/local/include
  /usr/include
)

# locate the library
IF(WIN32)
  SET(ZMQ_LIBRARY_NAMES ${ZMQ_LIBRARY_NAMES} libzmq.lib)
ELSE(WIN32)
  SET(ZMQ_LIBRARY_NAMES ${ZMQ_LIBRARY_NAMES} libzmq.a libzmq.so)
ENDIF(WIN32)

FIND_LIBRARY(ZMQ_LIBRARY
  NAMES ${ZMQ_LIBRARY_NAMES}
  PATHS ${ZMQ_HOME}/lib ${CMAKE_LIBRARY_PATH} /usr/lib /usr/local/lib
)

# try to locate the zmq_server
IF(WIN32)
  FIND_FILE(ZMQ_SERVER
    NAMES
    zmq_server.exe
    PATHS
    ${ZMQ_HOME}/bin
    ${CMAKE_BINARY_PATH}
    "[HKEY_CURRENT_USER\\zmq\\bin]"
    /usr/local/bin
    /usr/bin
    PATH_SUFFIXES
    bin
    DOC "Location of the zmq_server"
    )
ELSE(WIN32)
  FIND_FILE(ZMQ_SERVER
    NAMES
    zmq_server
    PATHS
    ${ZMQ_HOME}/bin
    ${CMAKE_BINARY_PATH}
    /usr/local/bin
    /usr/bin
    PATH_SUFFIXES
    bin
    DOC "Location of the zmq_server"
    )
ENDIF(WIN32)

# if the include and the program are found then we have it
if(ZMQ_LIBRARY AND ZMQ_INCLUDE_DIR)
  message(STATUS "Found ZeroMQ: I:${ZMQ_INCLUDE_DIR} L:${ZMQ_LIBRARY}")
  set(ZMQ_FOUND "YES")
else(ZMQ_LIBRARY AND ZMQ_INCLUDE_DIR)
  message(STATUS "ZeroMQ could not be found, try setting ZMQ_HOME (value=\"${ZMQ_HOME}\").")
endif(ZMQ_LIBRARY AND ZMQ_INCLUDE_DIR)

if(ZMQ_SERVER)
  message(STATUS "ZeroMQ-server found at: ${ZMQ_SERVER}")
endif(ZMQ_SERVER)

MARK_AS_ADVANCED(
  ZMQ_HOME
  ZMQ_SERVER
  ZMQ_LIBRARY
  ZMQ_INCLUDE_DIR
)


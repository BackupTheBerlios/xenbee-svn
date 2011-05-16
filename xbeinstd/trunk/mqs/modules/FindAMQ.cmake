# -*- mode: cmake; -*-
# Finds the activemq cpp staff
# Protocol Buffers is available at http://code.google.com/apis/protocolbuffers
# This file defines:
# * AMQ_FOUND if protoc was found
# * AMQ_LIBRARY The lib to link to (currently only a static unix lib, not portable) 

message(STATUS "FindAMQ check")
include(FindPackageHelper)
check_package(AMQ cms/Message.h activemq-cpp 2.1.3)

## call activemqcpp-config --version
set(AMQ_VERSION "2.1.3")

## activemq-cpp version check
string(REGEX REPLACE "^([0-9]+)\\.([0-9]+)\\.([0-9]+).*$" "\\10\\20\\3"
  AMQ_VERS ${AMQ_VERSION})
string(REGEX REPLACE "^([0-9]+)\\.([0-9]+).*$" "\\1"
  AMQ_VERSION_MAJOR ${AMQ_VERSION})
string(REGEX REPLACE "^([0-9]+)\\.([0-9]+).*" "\\2"
  AMQ_VERSION_MINOR ${AMQ_VERSION})

if( ${AMQ_VERSION} GREATER 30000)
  if (NOT WIN32)
    ## PkgConfig is helpful
    include(FindPkgConfig)

    pkg_check_modules(APR1 REQUIRED apr-1)
    set(APR1_STATIC_LDFLAGS "" CACHE INTERNAL "" FORCE)
    set(APR1_STATIC_LIBRARIES "" CACHE INTERNAL "" FORCE)
    include_directories(${APR1_INCLUDE_DIRS})

    pkg_check_modules(APRUTIL1 REQUIRED apr-util-1)
    set(APRUTIL1_STATIC_LDFLAGS "" CACHE INTERNAL "" FORCE)
    set(APRUTIL1_STATIC_LIBRARIES "" CACHE INTERNAL "" FORCE)
  endif (NOT WIN32)
endif( ${AMQ_VERSION} GREATER 30000)
if(NOT WIN32)
  set(AMQ_LIBRARY "${AMQ_LIBRARY};uuid")
endif(NOT WIN32)

message(STATUS "AMQ-Inc: ${AMQ_INCLUDE_DIR} ${AMQ_VERS}")


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

message(STATUS "AMQ-Inc: ${AMQ_INCLUDE_DIR} ${AMQ_VERS}")


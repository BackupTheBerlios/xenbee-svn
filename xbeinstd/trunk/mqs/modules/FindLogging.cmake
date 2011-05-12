# -*- mode: cmake; -*-
# Tries to locate a logging framework.
# This file defines:
# * LOG4CPP_FOUND if log4cpp was found
# * LOG4CPP_LIBRARIES The lib to link to (currently only a static unix lib, not portable) 
# * LOG4CPP_LIBRARY_DIRS The path to the library directory
# * LOG4CPP_INCLUDE_DIRS The path to the include directory

message(STATUS "FindLogging check")
include(FindPackageHelper)
check_package(LOG4CPP log4cpp/Category.hh log4cpp 1.0)

  if (LOG4CPP_FOUND)
    message(STATUS "log4cpp found")
  else(LOG4CPP_FOUND)
    message(STATUS "log4cpp NOT found")
  endif(LOG4CPP_FOUND)

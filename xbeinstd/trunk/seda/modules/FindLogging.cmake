# -*- mode: cmake; -*-
# Tries to locate a logging framework.
# This file defines:
# * LOG4CPP_FOUND if log4cpp was found
# * LOG4CPP_LIBRARIES The lib to link to (currently only a static unix lib, not portable) 
# * LOG4CPP_LIBRARY_DIRS The path to the library directory
# * LOG4CPP_INCLUDE_DIRS The path to the include directory

message(STATUS "FindLogging check")
IF (NOT WIN32)
  include(FindPkgConfig)
  if ( PKG_CONFIG_FOUND )

     pkg_check_modules (PC_LOG4CPP log4cpp>=1.0)

     set(LOG4CPP_DEFINITIONS ${PC_LOG4CPP_CFLAGS_OTHER})
  endif(PKG_CONFIG_FOUND)
endif (NOT WIN32)

#
# set defaults
SET(_log4cpp_HOME "/usr/local")
SET(_log4cpp_INCLUDE_SEARCH_DIRS
  ${CMAKE_INCLUDE_PATH}
  /usr/local/include
  /usr/include
  )

SET(_log4cpp_LIBRARIES_SEARCH_DIRS
  ${CMAKE_LIBRARY_PATH}
  /usr/local/lib
  /usr/lib
  )

##
if( "${LOG4CPP_HOME}" STREQUAL "")
  if("" MATCHES "$ENV{LOG4CPP_HOME}")
    message(STATUS "LOG4CPP_HOME env is not set, setting it to /usr/local")
    set (LOG4CPP_HOME ${_log4cpp_HOME})
  else("" MATCHES "$ENV{LOG4CPP_HOME}")
    set (LOG4CPP_HOME "$ENV{LOG4CPP_HOME}")
  endif("" MATCHES "$ENV{LOG4CPP_HOME}")
else( "${LOG4CPP_HOME}" STREQUAL "")
  message(STATUS "LOG4CPP_HOME is not empty: \"${LOG4CPP_HOME}\"")
endif( "${LOG4CPP_HOME}" STREQUAL "")
##

message(STATUS "Looking for log4cpp in ${LOG4CPP_HOME}")

IF( NOT ${LOG4CPP_HOME} STREQUAL "" )
    SET(_log4cpp_INCLUDE_SEARCH_DIRS ${LOG4CPP_HOME}/include ${_log4cpp_INCLUDE_SEARCH_DIRS})
    SET(_log4cpp_LIBRARIES_SEARCH_DIRS ${LOG4CPP_HOME}/lib ${_log4cpp_LIBRARIES_SEARCH_DIRS})
    SET(_log4cpp_HOME ${LOG4CPP_HOME})
ENDIF( NOT ${LOG4CPP_HOME} STREQUAL "" )

IF( NOT $ENV{LOG4CPP_INCLUDEDIR} STREQUAL "" )
  SET(_log4cpp_INCLUDE_SEARCH_DIRS $ENV{LOG4CPP_INCLUDEDIR} ${_log4cpp_INCLUDE_SEARCH_DIRS})
ENDIF( NOT $ENV{LOG4CPP_INCLUDEDIR} STREQUAL "" )

IF( NOT $ENV{LOG4CPP_LIBRARYDIR} STREQUAL "" )
  SET(_log4cpp_LIBRARIES_SEARCH_DIRS $ENV{LOG4CPP_LIBRARYDIR} ${_log4cpp_LIBRARIES_SEARCH_DIRS})
ENDIF( NOT $ENV{LOG4CPP_LIBRARYDIR} STREQUAL "" )

IF( LOG4CPP_HOME )
  SET(_log4cpp_INCLUDE_SEARCH_DIRS ${LOG4CPP_HOME}/include ${_log4cpp_INCLUDE_SEARCH_DIRS})
  SET(_log4cpp_LIBRARIES_SEARCH_DIRS ${LOG4CPP_HOME}/lib ${_log4cpp_LIBRARIES_SEARCH_DIRS})
  SET(_log4cpp_HOME ${LOG4CPP_HOME})
ENDIF( LOG4CPP_HOME )

# find the include files
FIND_PATH(LOG4CPP_INCLUDE_DIRS log4cpp/Category.hh
   HINTS
     ${_log4cpp_INCLUDE_SEARCH_DIRS}
     ${PC_LOG4CPP_INCLUDEDIR}
     ${PC_LOG4CPP_INCLUDE_DIRS}
    ${CMAKE_INCLUDE_PATH}
    $ENV{LOG4CPP_HOME}/include
)

# locate the library
SET(LOG4CPP_LIBRARY_NAMES ${LOG4CPP_LIBRARY_NAMES} liblog4cpp.a)
FIND_LIBRARY(LOG4CPP_LIBRARY NAMES ${LOG4CPP_LIBRARY_NAMES}
  HINTS
    ${_log4cpp_LIBRARIES_SEARCH_DIRS}
    ${PC_LOG4CPP_LIBDIR}
    ${PC_LOG4CPP_LIBRARY_DIRS}
    $ENV{LOG4CPP_HOME}/lib
)


# if the include and the program are found then we have it
IF(LOG4CPP_LIBRARY AND LOG4CPP_INCLUDE_DIRS) 
    message(STATUS "Found log4cpp: -I${LOG4CPP_INCLUDE_DIRS} ${LOG4CPP_LIBRARY}")
    GET_FILENAME_COMPONENT (LOG4CPP_LIBRARY_DIRS ${LOG4CPP_LIBRARY} PATH)
    GET_FILENAME_COMPONENT (LOG4CPP_LIBRARIES ${LOG4CPP_LIBRARY} NAME)
    SET(LOG4CPP_FOUND "YES")
ENDIF(LOG4CPP_LIBRARY AND LOG4CPP_INCLUDE_DIRS)

  message("  LOG4CPP 1: -I${LOG4CPP_STATIC_INCLUDE_DIRS} -L${LOG4CPP_STATIC_LIBRARY_DIRS} -l${LOG4CPP_STATIC_LIBRARIES}")
  message("  LOG4CPP 2: -I${LOG4CPP_INCLUDE_DIRS} -L${LOG4CPP_LIBRARY_DIRS} ${LOG4CPP_LIBRARIES} ${LOG4CPP_LIBRARY}")

set(LOG4CPP_STATIC_INCLUDE_DIRS ${LOG4CPP_INCLUDE_DIRS} PARENT_SCOPE)
set(LOG4CPP_STATIC_LIBRARY_DIRS ${LOG4CPP_LIBRARY_DIRS} PARENT_SCOPE)
set(LOG4CPP_STATIC_LIBRARIES ${LOG4CPP_LIBRARIES} PARENT_SCOPE)

MARK_AS_ADVANCED(
  LOG4CPP_LIBRARY
  LOG4CPP_LIBRARIES
  LOG4CPP_LIBRARY_DIRS
  LOG4CPP_INCLUDE_DIRS
)

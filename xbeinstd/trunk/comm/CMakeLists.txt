# -*- mode: cmake; -*-
project(libcomm)

# have the full monty in makefiles
set(CMAKE_VERBOSE_MAKEFILE true)

set(V_MAJOR 1)
set(V_MINOR 1)
set(V_PATCH 0)

# add a path where some libraries might be stored
set(CMAKE_ADDITIONAL_PATH $ENV{CMAKE_ADDITIONAL_PATH} CACHE PATH "Path where many locally installed libraries can be found")

###################################################################################################
# No user settings below
###################################################################################################

OPTION(ENABLE_LOGGING
  "Build the project with logging enabled"
  YES)

OPTION(ENABLE_UNIT_TESTS
  "Build and perform unit tests"
  YES)

cmake_minimum_required(VERSION "2.6" FATAL_ERROR)
# Where are the additional libraries installed? Note: provide includes
# path here, subsequent checks will resolve everything else
set(CMAKE_INCLUDE_PATH ${CMAKE_INCLUDE_PATH} ${CMAKE_ADDITIONAL_PATH}/include)
set(CMAKE_LIBRARY_PATH ${CMAKE_LIBRARY_PATH} ${CMAKE_ADDITIONAL_PATH}/lib)
set(CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/modules")

# Definitions for different compilations.
# Debug is the default development mode. Warn as much as possible, but
# CPPUnit raises some errors about virtual functions - suppress them.
if (UNIX)
  set(CMAKE_CXX_FLAGS_DEBUG "-Wall -Werror -Wno-non-virtual-dtor" CACHE STRING "compiler flags - debug")
  # Releases are made with the release build. Optimize code.
  set(CMAKE_CXX_FLAGS_RELEASE "-Wall -Werror -O3 -Wno-non-virtual-dtor" CACHE STRING "compiler flags - release")
  set(CMAKE_CXX_FLAGS "-Wall -Werror -O3 -Wno-non-virtual-dtor" CACHE STRING "compiler flags")
else(UNIX)
  # make windows happy
endif(UNIX)

## PkgConfig is helpful
include(FindPkgConfig)
if ( PKG_CONFIG_FOUND )
  pkg_check_modules (CPPUNIT cppunit>=1.12)
  message(STATUS "CPPUnit: ${CPPUNIT_CFLAGS} ${CPPUNIT_LDFLAGS} STATIC=${CPPUNIT_STATIC_LDFLAGS}")
  pkg_check_modules (LOG4CPP log4cpp>=1.0)
  # The log4cpp package config is broken, doesn't set static library -
  # therefore do it manually here.
  set(LOG4CPP_STATIC_LIBRARIES log4cpp.a)
  message(STATUS "LOG4CPP: ${LOG4CPP_CFLAGS} ${LOG4CPP_LDFLAGS} STATIC=${LOG4CPP_STATIC_LDFLAGS}")

  pkg_check_modules (SEDA REQUIRED libseda>=1.1)
  message(STATUS "SEDA: -I${SEDA_INCLUDE_DIRS} -L${SEDA_LIBRARY_DIRS} -l${SEDA_LIBRARIES}")

else  ( PKG_CONFIG_FOUND )
  message("No PKGCONFIG found - hoping for the best.")

  set(CPPUNIT_INCLUDE_DIRS "${CMAKE_ADDITIONAL_PATH}/include" CACHE PATH "CPPUnit Include dir")
  set(CPPUNIT_LIBRARY_DIRS "${CMAKE_ADDITIONAL_PATH}/lib" CACHE PATH "CPPUnit Library dir")
  set(CPPUNIT_LIBRARIES "cppunit" CACHE PATH "CPPUnit libraries")

  set(LOG4CPP_STATIC_INCLUDE_DIRS "${CMAKE_ADDITIONAL_PATH}/include" CACHE PATH "Log4cpp Include dir")
  set(LOG4CPP_STATIC_LIBRARY_DIRS "${CMAKE_ADDITIONAL_PATH}/lib" CACHE PATH "Log4cpp Library dir")
  set(LOG4CPP_STATIC_LIBRARIES    "log4cpp" CACHE STRING "Log4cpp libraries")
  set(LOG4CPP_FOUND NO CACHE BOOL "Log4cpp found")
endif ( PKG_CONFIG_FOUND )

## check for threads
Include(FindThreads)

if (CMAKE_USE_PTHREADS_INIT)
  set (HAVE_PTHREAD_H 1)
endif (CMAKE_USE_PTHREADS_INIT)

## check for boost
set(BOOST_ROOT "${CMAKE_ADDITIONAL_PATH}" CACHE PATH "Where to find the Boost libraries")
set(Boost_ADDITIONAL_VERSIONS "1.37.0" "1.37" "1.36.0" "1.36")
set(Boost_FIND_QUIETLY false)
set(Boost_USE_STATIC_LIBS ON)
include(FindBoost)
find_package(Boost 1.36 REQUIRED COMPONENTS thread)
# we need at least 1.36 so check for it
if (Boost_MAJOR_VERSION LESS 1)
    message(FATAL_ERROR "At least Boost 1.36 is required")
endif(Boost_MAJOR_VERSION LESS 1)
if (Boost_MINOR_VERSION LESS 36)
    message(FATAL_ERROR "At least Boost 1.36 is required")
endif (Boost_MINOR_VERSION LESS 36)
message(STATUS "Boost: -I${Boost_INCLUDE_DIRS} -L${Boost_LIBRARY_DIRS} -l${Boost_LIBRARIES}")


# google protocol buffers
Include(FindProtocolBuffers)
if (PB_FOUND)
    message(STATUS "Found Protocol Buffers: ${PB_PROTOC_CMD}")
endif (PB_FOUND)
Include(PBMacros)

# Deal with logging
if(ENABLE_LOGGING)
  set(ENABLE_LOGGING 1)
  if (LOG4CPP_FOUND)
    set(HAVE_LOG4CPP 1)
    message(STATUS "Building with logging enabled.")
  else (LOG4CPP_FOUND)
    set(HAVE_LOG4CPP)
    message(STATUS "Failed to find log4cpp. Deactivating logging.")
  endif (LOG4CPP_FOUND)
else(ENABLE_LOGGING)
  message("Disabled logging by request.")
  set(ENABLE_LOGGING)
endif(ENABLE_LOGGING)

configure_file(${CMAKE_CURRENT_SOURCE_DIR}/config.h.in    ${CMAKE_CURRENT_BINARY_DIR}/config.h)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/libcomm.pc.in   ${CMAKE_CURRENT_BINARY_DIR}/libcomm.pc)

ADD_DEFINITIONS( -DHAVE_CONFIG_H )

# Make sure all subdirectories include correctly
include_directories(${CMAKE_CURRENT_BINARY_DIR})
include_directories(${${PROJECT_NAME}_SOURCE_DIR})
include_directories(${LOG4CPP_STATIC_INCLUDE_DIRS})
include_directories(${Boost_INCLUDE_DIRS})

include_directories(${CMAKE_INCLUDE_PATH})
link_directories(${CMAKE_LIBRARY_PATH} ${LOG4CPP_STATIC_LIBRARY_DIRS})
link_directories(${${PROJECT_NAME}_BINARY_DIR})
link_directories(${Boost_LIBRARY_DIRS})
if (CMAKE_USE_PTHREADS_INIT)
    link_libraries(-lpthread)
endif(CMAKE_USE_PTHREADS_INIT)
link_libraries(${Boost_LIBRARIES})
if(ENABLE_LOGGING)
  link_libraries(-Wl,-Bstatic ${LOG4CPP_STATIC_LIBRARIES})
endif(ENABLE_LOGGING)

# Reflect the package structure
add_subdirectory(comm)

if (ENABLE_UNIT_TESTS)
  enable_testing()
  add_subdirectory(tests)
endif (ENABLE_UNIT_TESTS)

# add some files to the installation target
INSTALL(FILES INSTALL README COPYING ChangeLog NEWS DESTINATION
  share/doc/${PROJECT_NAME}-${V_MAJOR}.${V_MINOR}
  )

# install pkgconfig file
install(FILES ${CMAKE_CURRENT_BINARY_DIR}/libcomm.pc
  DESTINATION lib/pkgconfig
  )

# CPACK packaging
INCLUDE(InstallRequiredSystemLibraries)
SET(CPACK_PACKAGE_DESCRIPTION_SUMMARY "Communication C++ library")
SET(CPACK_PACKAGE_VENDOR "Fraunhofer ITWM")
SET(CPACK_PACKAGE_CONTACT "petry@itwm.fhg.de")
SET(CPACK_PACKAGE_DESCRIPTION_FILE "${CMAKE_CURRENT_SOURCE_DIR}/README")
SET(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_CURRENT_SOURCE_DIR}/COPYING")
SET(CPACK_PACKAGE_VERSION_MAJOR ${V_MAJOR})
SET(CPACK_PACKAGE_VERSION_MINOR ${V_MINOR})
SET(CPACK_PACKAGE_VERSION_PATCH ${V_PATCH})
SET(CPACK_PACKAGE_INSTALL_DIRECTORY "CMake ${CMake_VERSION_MAJOR}.${CMake_VERSION_MINOR}")

SET(CPACK_GENERATOR "DEB;RPM;STGZ;TGZ;TBZ2")

IF(WIN32 AND NOT UNIX)
  # There is a bug in NSI that does not handle full unix paths properly. Make
  # sure there is at least one set of four (4) backlasshes.
  SET(CPACK_PACKAGE_ICON "${CMake_SOURCE_DIR}/Utilities/Release\\\\InstallIcon.bmp")
  SET(CPACK_NSIS_INSTALLED_ICON_NAME "bin\\\\MyExecutable.exe")
  SET(CPACK_NSIS_DISPLAY_NAME "${CPACK_PACKAGE_INSTALL_DIRECTORY} Communication C++ library")
  SET(CPACK_NSIS_HELP_LINK "http:\\\\\\\\www.xenbee.net")
  SET(CPACK_NSIS_URL_INFO_ABOUT "http:\\\\\\\\www.xenbee.net")
  SET(CPACK_NSIS_CONTACT "petry@itwm.fhg.de")
  SET(CPACK_NSIS_MODIFY_PATH ON)
ELSE(WIN32 AND NOT UNIX)
  SET(CPACK_SOURCE_STRIP_FILES "")
ENDIF(WIN32 AND NOT UNIX)
INCLUDE(CPack)

### print some output for the user
message("***** Configuration *****")
message("  prefix: ${CMAKE_INSTALL_PREFIX}")
if (ENABLE_LOGGING)
  message("  logging: yes")
  message("  LOG4CPP: -I${LOG4CPP_STATIC_INCLUDE_DIRS} -L${LOG4CPP_STATIC_LIBRARY_DIRS} -l${LOG4CPP_STATIC_LIBRARIES}")
else (ENABLE_LOGGING)
  message("  logging: no")
endif (ENABLE_LOGGING)
if (ENABLE_UNIT_TESTS)
  message("  unit tests: yes")
  message("  CPPUnit: -I${CPPUNIT_INCLUDE_DIRS} -L${CPPUNIT_LIBRARY_DIRS} -l${CPPUNIT_LIBRARIES}")
else (ENABLE_UNIT_TESTS)
  message("  unit tests: no")
endif (ENABLE_UNIT_TESTS)
message("")
message("Additional libraries:")
message("  Boost: -I${Boost_INCLUDE_DIRS} -L${Boost_LIBRARY_DIRS}")
message("Additional tools")
message("----------------")
message("")
message("   pb: ${PB_PROTOC_CMD}")
message("")


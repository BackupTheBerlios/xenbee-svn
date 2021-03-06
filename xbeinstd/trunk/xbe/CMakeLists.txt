# -*- mode: cmake; -*-
project(libxbe)

# have the full monty in makefiles
set(CMAKE_VERBOSE_MAKEFILE true)

set(V_MAJOR 0)
set(V_MINOR 1)
set(V_PATCH 0)

# add a path where some libraries might be stored
set(CMAKE_ADDITIONAL_PATH $ENV{CMAKE_ADDITIONAL_PATH} CACHE PATH "Path where many locally installed libraries can be found")

###################################################################################################
# No user settings below
###################################################################################################

OPTION(ENABLE_LOGGING
  "Build the project with logging enabled"
  ON)

OPTION(ENABLE_UNIT_TESTS
  "Build and perform unit tests"
  ON)

set(TEST_BROKER_URI "tcp://localhost:61613?wireFormat=stomp&username=guest&password=guest" CACHE STRING "The ActiveMQ broker to use for unit tests")

cmake_minimum_required(VERSION "2.6" FATAL_ERROR)
# Where are the additional libraries installed? Note: provide includes
# path here, subsequent checks will resolve everything else
set(CMAKE_INCLUDE_PATH ${CMAKE_INCLUDE_PATH} ${CMAKE_ADDITIONAL_PATH}/include)
set(CMAKE_LIBRARY_PATH ${CMAKE_LIBRARY_PATH} ${CMAKE_ADDITIONAL_PATH}/lib)
set(CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/modules")

# Definitions for different compilations.
# Debug is the default development mode. Warn as much as possible, but
# CPPUnit raises some errors about virtual functions - suppress them.
set(CMAKE_CXX_FLAGS_DEBUG "-Wall -Werror -Wno-non-virtual-dtor")
# Releases are made with the release build. Optimize code.
set(CMAKE_CXX_FLAGS_RELEASE "-Wall -Werror -O3 -Wno-non-virtual-dtor")
set(CMAKE_CXX_FLAGS "-Wall -Werror -O3 -Wno-non-virtual-dtor")

#set(LINK_FLAGS "-Wl,-Bdynamic")
set(USE_STATIC ON)
#set(CMAKE_EXE_LINKER_FLAGS "-static")

## PkgConfig is helpful
include(FindPkgConfig)
if ( PKG_CONFIG_FOUND )
   pkg_check_modules (CPPUNIT cppunit>=1.12)
   message(STATUS "CPPUnit: ${CPPUNIT_CFLAGS} ${CPPUNIT_LDFLAGS} STATIC=${CPPUNIT_STATIC_LDFLAGS}")
   pkg_check_modules (LOG4CPP log4cpp>=1.0)

   pkg_check_modules (MQS REQUIRED libmqs>=0.1)
   message(STATUS "MQS: -I${MQS_INCLUDE_DIRS} -L${MQS_LIBRARY_DIRS} -l${MQS_LIBRARIES}")

   pkg_check_modules (SEDA REQUIRED libseda>=1.1)
   message(STATUS "SEDA: -I${SEDA_INCLUDE_DIRS} -L${SEDA_LIBRARY_DIRS} -l${SEDA_LIBRARIES}")

   # The log4cpp package config is broken, doesn't set static library -
   # therefore do it manually here.
   set(LOG4CPP_STATIC_LIBRARIES log4cpp.a)
   message(STATUS "LOG4CPP: ${LOG4CPP_CFLAGS} ${LOG4CPP_LDFLAGS} STATIC=${LOG4CPP_STATIC_LDFLAGS}")

   pkg_check_modules(AMQ REQUIRED activemq-cpp>=2.1.3)
   message(STATUS "ActiveMQ: ${AMQ_CFLAGS} ${AMQ_LDFLAGS} STATIC=${AMQ_STATIC_LDFLAGS}")
else  ( PKG_CONFIG_FOUND )
  message(FATAL_ERROR "No PKGCONFIG found - hoping for the best.")
endif ( PKG_CONFIG_FOUND )

## check for threads
Include(FindThreads)

## find xsd and xerces-c
#Include(FindXsd)
#if (NOT XSD_FOUND)
#    message(FATAL_ERROR "Could not find the XSD Schema Compiler, this is a required tool for this package! Check modules/FindXSD.cmake for more information.")
#endif(NOT XSD_FOUND)
#Include(XsdMacros)

#Include(FindXercesC)
#Include(FindXMLSecurityC)

## find the StateMachineCompiler (SMC)
Include(FindSMC)
if (SMC_FOUND)
    message(STATUS "Found StateMachineCompiler: ${SMC_JAR}")
else(SMC_FOUND)
    message(FATAL_ERROR "Could not find the State Machine Compiler, this is a required tool for this package! Maybe set SMC_HOME correctly.")
endif(SMC_FOUND)
Include(SMCMacros)

Include(FindProtocolBuffers)
if (PB_FOUND)
    message(STATUS "Found Protocol Buffers: ${PB_PROTOC_CMD}")
#else(PB_FOUND)
#    message(FATAL_ERROR "Could not find the ProtocolBuffers package. Maybe set PROTOC_HOME correctly.")
endif (PB_FOUND)
Include(PBMacros)


#if (XERCESC_FOUND)
#  message(STATUS "Xerces-C: -I${XERCESC_INCLUDE_DIR} ${XERCESC_LIBRARIES}")
#else(XERCESC_FOUND )
#  message(FATAL_ERROR "Xerces-C could not be found!")
#endif(XERCESC_FOUND )

#if (XMLSecurityC_FOUND)
#  message(STATUS "XML-Security-C: -I${XMLSecurityC_INCLUDE_DIR} ${XMLSecurityC_LIBRARIES}")
#else(XMLSecurityC_FOUND )
#  message(FATAL_ERROR "XML-Security-C could not be found!")
#endif(XMLSecurityC_FOUND )

if (CMAKE_USE_PTHREADS_INIT)
  set (HAVE_PTHREAD_H 1)
endif (CMAKE_USE_PTHREADS_INIT)

## check for boost
set(BOOST_ROOT "${ADDITIONAL_CMAKE_PATH}" CACHE PATH "")
set(Boost_ADDITIONAL_VERSIONS "1.36.0" "1.36")
set(Boost_FIND_QUIETLY false)
set(Boost_USE_STATIC_LIBS ON)
include(FindBoost)
find_package(Boost 1.36 REQUIRED COMPONENTS thread system filesystem program_options)
message(STATUS "Boost: -I${Boost_INCLUDE_DIRS} -L${Boost_LIBRARY_DIRS} -l${Boost_LIBRARIES}")

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

set(INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

configure_file(${CMAKE_CURRENT_SOURCE_DIR}/config.h.in    ${CMAKE_CURRENT_BINARY_DIR}/config.h)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/libxbe.pc.in   ${CMAKE_CURRENT_BINARY_DIR}/libxbe.pc)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/etc/xbe/xbeinstd.rc.in ${CMAKE_CURRENT_BINARY_DIR}/etc/xbe/xbeinstd.rc)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/etc/init.d/xbeinstd.in ${CMAKE_CURRENT_BINARY_DIR}/etc/init.d/xbeinstd)

ADD_DEFINITIONS( -DHAVE_CONFIG_H )

# Make sure all subdirectories include correctly
include_directories(${CMAKE_CURRENT_BINARY_DIR})
include_directories(${${PROJECT_NAME}_SOURCE_DIR})
include_directories(${LOG4CPP_STATIC_INCLUDE_DIRS})
#include_directories(${XERCESC_INCLUDE_DIR})
#include_directories(${XMLSecurityC_INCLUDE_DIR})
include_directories(${MQS_INCLUDE_DIRS})
include_directories(${SEDA_INCLUDE_DIRS})
include_directories(${AMQ_INCLUDE_DIRS})
include_directories(${SMC_INCLUDE_DIR})
#include_directories(${XSD_INCLUDE_DIR})
include_directories(${Boost_INCLUDE_DIR})
include_directories(${CMAKE_INCLUDE_PATH})

link_directories(${CMAKE_LIBRARY_PATH} ${LOG4CPP_STATIC_LIBRARY_DIRS})
link_directories(${${PROJECT_NAME}_BINARY_DIR})
link_directories(${SEDA_LIBRARY_DIRS})
link_directories(${MQS_LIBRARY_DIRS})
link_directories(${AMQ_LIBRARY_DIRS})
link_directories(${Boost_LIBRARY_DIRS})
link_libraries(-lmqs -lseda)
if (CMAKE_USE_PTHREADS_INIT)
    link_libraries(-lpthread)
endif(CMAKE_USE_PTHREADS_INIT)
link_libraries(${Boost_LIBRARIES})
link_libraries(${SEDA_LIBRARIES})
link_libraries(${MQS_LIBRARIES})
link_libraries(${PB_LIBRARY})
link_libraries(-Wl,-Bstatic ${AMQ_STATIC_LDFLAGS} -Wl,-Bdynamic)
#link_libraries(${XERCESC_LIBRARIES})
#link_libraries(-Wl,-Bdynamic -lxalan-c)
#link_libraries(${XMLSecurityC_LIBRARIES})

if(XSD_FOUND)
  include_directories(${XSD_INCLUDE_DIR})
endif(XSD_FOUND)

if(ENABLE_LOGGING)
  link_libraries(${LOG4CPP_STATIC_LIBRARIES})
endif(ENABLE_LOGGING)

# Reflect the package structure
add_subdirectory(xbe/common)
add_subdirectory(xbe)
add_subdirectory(xbeinstd)

if (ENABLE_UNIT_TESTS)
  enable_testing()
  add_subdirectory(tests)
endif (ENABLE_UNIT_TESTS)

# add some files to the installation target
INSTALL(FILES INSTALL README COPYING ChangeLog NEWS xbe/xbemsg.proto DESTINATION
  share/doc/${PROJECT_NAME}-${V_MAJOR}.${V_MINOR}
)

#pkgconfig file
INSTALL(FILES ${CMAKE_CURRENT_BINARY_DIR}/libxbe.pc
  DESTINATION lib/pkgconfig
)

install(FILES ${CMAKE_CURRENT_BINARY_DIR}/etc/xbe/xbeinstd.rc DESTINATION etc/xbe)
install(FILES ${CMAKE_CURRENT_BINARY_DIR}/etc/init.d/xbeinstd DESTINATION etc/init.d
    PERMISSIONS
    OWNER_WRITE OWNER_READ OWNER_EXECUTE
    GROUP_READ GROUP_EXECUTE
    WORLD_READ WORLD_EXECUTE)
install(FILES ${CMAKE_CURRENT_BINARY_DIR}/config.h RENAME xbe-config.h DESTINATION include/xbe)

# CPACK packaging
INCLUDE(InstallRequiredSystemLibraries)
SET(CPACK_PACKAGE_DESCRIPTION_SUMMARY "XenBEE C++ library")
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
  SET(CPACK_NSIS_DISPLAY_NAME "${CPACK_PACKAGE_INSTALL_DIRECTORY} XenBEE C++ library")
  SET(CPACK_NSIS_HELP_LINK "http:\\\\\\\\www.xenbee.net")
  SET(CPACK_NSIS_URL_INFO_ABOUT "http:\\\\\\\\www.xenbee.net")
  SET(CPACK_NSIS_CONTACT "petry@itwm.fhg.de")
  SET(CPACK_NSIS_MODIFY_PATH ON)
ELSE(WIN32 AND NOT UNIX)
  SET(CPACK_SOURCE_STRIP_FILES "")
ENDIF(WIN32 AND NOT UNIX)
INCLUDE(CPack)

### print some output for the user
message("")
message("************************************")
message("***** Configuration parameters *****")
message("************************************")
message("")
message("  prefix: ${CMAKE_INSTALL_PREFIX}")
message("  broker: ${TEST_BROKER_URI}")
message("")
if (ENABLE_LOGGING)
message("  logging: yes")
message("    LOG4CPP: ${LOG4CPP_CFLAGS} ${LOG4CPP_LDFLAGS} STATIC=${LOG4CPP_STATIC_LDFLAGS}")
else (ENABLE_LOGGING)
message("  logging: no")
endif (ENABLE_LOGGING)
if (ENABLE_UNIT_TESTS)
message("  unit tests: yes")
message("    CPPUnit: ${CPPUNIT_CFLAGS} ${CPPUNIT_LDFLAGS} STATIC=${CPPUNIT_STATIC_LDFLAGS}")
else (ENABLE_UNIT_TESTS)
message("  unit tests: no")
endif (ENABLE_UNIT_TESTS)
message("")
message("Additional libraries")
message("--------------------")
message("")
message("  AMQ: -I${AMQ_INCLUDE_DIRS} -L${AMQ_LIBRARY_DIRS} -l${AMQ_LIBRARIES}")
#message("  Xerces-C: -I${XERCESC_INCLUDE_DIR} -l${XERCESC_LIBRARIES}")
#message("  XML-Security-C: -I${XMLSecurityC_INCLUDE_DIR} -l${XMLSecurityC_LIBRARIES}")
message("")
message("Additional tools")
message("----------------")
message("")
message("  smc: ${SMC_JAR}")
#message("  xsd: ${XSD_EXECUTABLE} -I${XSD_INCLUDE_DIR}")
message("   pb: ${PB_PROTOC_CMD}")
message("")

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

set(TEST_BROKER_URI "tcp://localhost:61616" CACHE STRING "The ActiveMQ broker to use for unit tests")

cmake_minimum_required(VERSION "2.6" FATAL_ERROR)
# Where are the additional libraries installed? Note: provide includes
# path here, subsequent checks will resolve everything else
set(CMAKE_INCLUDE_PATH ${CMAKE_INCLUDE_PATH} ${CMAKE_ADDITIONAL_PATH}/include)
set(CMAKE_LIBRARY_PATH ${CMAKE_LIBRARY_PATH} ${CMAKE_ADDITIONAL_PATH}/lib)
set(CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/modules")

# Definitions for different compilations.
# Debug is the default development mode. Warn as much as possible, but
# CPPUnit raises some errors about virtual functions - suppress them.
set(CMAKE_CXX_FLAGS_DEBUG "-Wall -Wno-non-virtual-dtor")
# Releases are made with the release build. Optimize code.
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -Wno-non-virtual-dtor")

## PkgConfig is helpful
include(FindPkgConfig)
if ( PKG_CONFIG_FOUND )
   pkg_check_modules (CPPUNIT cppunit>=1.12)
   message(STATUS "CPPUnit: -I${CPPUNIT_INCLUDE_DIRS} -L${CPPUNIT_LIBRARY_DIRS} -l${CPPUNIT_LIBRARIES}")
   pkg_check_modules (LOG4CPP log4cpp>=1.0)
   # The log4cpp package config is broken, doesn't set static library -
   # therefore do it manually here.
   set(LOG4CPP_STATIC_LIBRARIES log4cpp.a)
   message(STATUS "LOG4CPP: -I${LOG4CPP_STATIC_INCLUDE_DIRS} -L${LOG4CPP_STATIC_LIBRARY_DIRS} -l${LOG4CPP_STATIC_LIBRARIES}")

   pkg_check_modules(AMQ REQUIRED activemq-cpp>=2.1.3)
   message(STATUS "ActiveMQ: -I${AMQ_INCLUDE_DIRS} -L${AMQ_LIBRARY_DIRS} -l${AMQ_LIBRARIES}")
else  ( PKG_CONFIG_FOUND )
  message(FATAL_ERROR "No PKGCONFIG found - hoping for the best.")
endif ( PKG_CONFIG_FOUND )

## check for threads
Include(FindThreads)

## find xsd and xerces-c
Include(FindXsd)
Include(XsdMacros)
Include(FindXercesC)
Include(FindXMLSecurityC)

## find the StateMachineCompiler (SMC)
Include(FindSMC)
Include(SMCMacros)

if (XERCESC_FOUND)
  message(STATUS "Xerces-C: -I${XERCESC_INCLUDE_DIR} ${XERCESC_LIBRARIES}")
else(XERCESC_FOUND )
  message(FATAL_ERROR "Xerces-C could not be found!")
endif(XERCESC_FOUND )

if (XMLSecurityC_FOUND)
  message(STATUS "XML-Security-C: -I${XMLSecurityC_INCLUDE_DIR} ${XMLSecurityC_LIBRARIES}")
else(XMLSecurityC_FOUND )
  message(FATAL_ERROR "XML-Security-C could not be found!")
endif(XMLSecurityC_FOUND )

if (CMAKE_USE_PTHREADS_INIT)
  set (HAVE_PTHREAD_H 1)
endif (CMAKE_USE_PTHREADS_INIT)

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
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/libxbe.pc.in   ${CMAKE_CURRENT_BINARY_DIR}/libxbe.pc)

ADD_DEFINITIONS( -DHAVE_CONFIG_H )

# Make sure all subdirectories include correctly
include_directories(${CMAKE_CURRENT_BINARY_DIR} ${LOG4CPP_STATIC_INCLUDE_DIRS})
include_directories(${CMAKE_INCLUDE_PATH})
include_directories(${${PROJECT_NAME}_SOURCE_DIR})
include_directories(${XERCESC_INCLUDE_DIR})
include_directories(${XMLSecurityC_INCLUDE_DIR})
include_directories(${AMQ_INCLUDE_DIRS})
include_directories(${SMC_INCLUDE_DIR})
include_directories(${XSD_INCLUDE_DIR})

link_directories(${CMAKE_LIBRARY_PATH} ${LOG4CPP_STATIC_LIBRARY_DIRS})
link_directories(${${PROJECT_NAME}_BINARY_DIR})
link_directories(${AMQ_LIBRARY_DIRS})
link_libraries(-lcrypto -lpthread -lmqs -lseda)
link_libraries(-Wl,-Bstatic ${AMQ_STATIC_LIBRARIES})
link_libraries(-Wl,-Bdynamic ${XERCESC_LIBRARIES})
link_libraries(-Wl,-Bdynamic -lxalan-c)
link_libraries(${XMLSecurityC_LIBRARIES})

if(XSD_FOUND)
  include_directories(${XSD_INCLUDE_DIR})
endif(XSD_FOUND)

if(ENABLE_LOGGING)
  link_libraries(${LOG4CPP_STATIC_LIBRARIES})
endif(ENABLE_LOGGING)

# Reflect the package structure
add_subdirectory(xbe)

if (ENABLE_UNIT_TESTS)
  enable_testing()
  add_subdirectory(tests)
endif (ENABLE_UNIT_TESTS)

# add some files to the installation target
INSTALL(FILES INSTALL README COPYING ChangeLog NEWS DESTINATION
  share/doc/${PROJECT_NAME}-${V_MAJOR}.${V_MINOR}
)

#pkgconfig file
INSTALL(FILES ${CMAKE_CURRENT_BINARY_DIR}/libmqs.pc
  DESTINATION lib/pkgconfig
)

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
message("    LOG4CPP: -I${LOG4CPP_STATIC_INCLUDE_DIRS} -L${LOG4CPP_STATIC_LIBRARY_DIRS} -l${LOG4CPP_STATIC_LIBRARIES}")
else (ENABLE_LOGGING)
message("  logging: no")
endif (ENABLE_LOGGING)
if (ENABLE_UNIT_TESTS)
message("  unit tests: yes")
message("    CPPUnit: -I${CPPUNIT_INCLUDE_DIRS} -L${CPPUNIT_LIBRARY_DIRS} -l${CPPUNIT_LIBRARIES}")
else (ENABLE_UNIT_TESTS)
message("  unit tests: no")
endif (ENABLE_UNIT_TESTS)
message("")
message("Additional libraries")
message("--------------------")
message("")
message("  AMQ: -I${AMQ_INCLUDE_DIRS} -L${AMQ_LIBRARY_DIRS} -l${AMQ_LIBRARIES}")
message("  Xerces-C: -I${XERCESC_INCLUDE_DIR} -l${XERCESC_LIBRARIES}")
message("  XML-Security-C: -I${XMLSecurityC_INCLUDE_DIR} -l${XMLSecurityC_LIBRARIES}")
message("")
message("Additional tools")
message("----------------")
message("")
message("  smc: ${SMC_JAR}")
message("  xsd: ${XSD_EXECUTABLE} -I${XSD_INCLUDE_DIR}")
message("")

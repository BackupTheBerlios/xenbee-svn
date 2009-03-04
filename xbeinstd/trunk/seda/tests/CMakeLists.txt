# -*- mode: cmake; -*-

# add the CPPUNIT stuff
include_directories(${CPPUNIT_INCLUDE_DIRS})
link_directories(${CPPUNIT_LIBRARY_DIRS})
link_libraries(${CPPUNIT_LIBRARIES})

#file(GLOB dirs "${CMAKE_CURRENT_SOURCE_DIR}/*")
add_subdirectory("seda")

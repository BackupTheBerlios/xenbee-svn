# -*- mode: cmake; -*-

# add the CPPUNIT stuff
include_directories(${CPPUNIT_INCLUDE_DIRS})
link_directories(${CPPUNIT_LIBRARY_DIRS})
link_libraries(-Wl,-Bstatic ${CPPUNIT_STATIC_LDFLAGS} -Wl,-Bdynamic)

file(GLOB dirs "${CMAKE_CURRENT_SOURCE_DIR}/*")
foreach(DIR ${dirs})
  if(IS_DIRECTORY ${DIR})
     add_subdirectory(${DIR})
  endif(IS_DIRECTORY ${DIR})
endforeach(DIR)

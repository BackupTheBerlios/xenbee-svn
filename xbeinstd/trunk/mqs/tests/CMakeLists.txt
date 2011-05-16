# -*- mode: cmake; -*-

# add the CPPUNIT stuff
include_directories(${CPPUNIT_INCLUDE_DIR})
link_directories(${CPPUNIT_LIBRARY_DIR})
if(WIN32)
  link_libraries(${CPPUNIT_LIBRARY})
else(WIN32)
  if(CPPUNIT_STATIC_LIBS STREQUAL "")
    link_libraries(${CPPUNIT_LIBRARIES} dl)
  else(CPPUNIT_STATIC_LIBS STREQUAL "")
    link_libraries(-Wl,-Bstatic ${CPPUNIT_STATIC_LDFLAGS} -Wl,-Bdynamic)
  endif(CPPUNIT_STATIC_LIBS STREQUAL "")
endif(WIN32)

set(dirs "mqs;")
foreach(DIR ${dirs})
  if(IS_DIRECTORY ${DIR})
     add_subdirectory(${DIR})
  endif(IS_DIRECTORY ${DIR})
endforeach(DIR)

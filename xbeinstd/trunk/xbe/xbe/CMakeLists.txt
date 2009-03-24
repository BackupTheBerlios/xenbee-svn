# -*- mode: cmake; -*-
file(GLOB hdrs1 "${CMAKE_CURRENT_SOURCE_DIR}/*.hpp")
file(GLOB hdrs2 "${CMAKE_CURRENT_SOURCE_DIR}/event/*.hpp")
file(GLOB srcs "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp" "${CMAKE_CURRENT_SOURCE_DIR}/event/*.cpp")

add_protocol_buffers(xbemsg)
list(APPEND srcs "${CMAKE_CURRENT_SOURCE_DIR}/xbemsg.pb.cc")
list(APPEND hdrs1 "${CMAKE_CURRENT_SOURCE_DIR}/xbemsg.pb.h")

add_state_machine(XbeInstd srcs hdrs)
list(APPEND srcs "${CMAKE_CURRENT_SOURCE_DIR}/XbeInstd_sm.cpp")
list(APPEND hdrs1 "${CMAKE_CURRENT_SOURCE_DIR}/XbeInstd_sm.h")

list(REMOVE_DUPLICATES hdrs1)
list(REMOVE_DUPLICATES hdrs2)
list(REMOVE_DUPLICATES srcs)

add_subdirectory(common)

ADD_LIBRARY(xbe ${srcs})

install(FILES ${hdrs1} DESTINATION include/xbe)
install(FILES ${hdrs2} DESTINATION include/xbe/event)
install(TARGETS xbe
	ARCHIVE DESTINATION lib)

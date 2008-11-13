# -*- mode: cmake; -*-
file(GLOB hdrs "${CMAKE_CURRENT_SOURCE_DIR}/*.hpp" "${CMAKE_CURRENT_SOURCE_DIR}/event/*.hpp")
file(GLOB srcs "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp" "${CMAKE_CURRENT_SOURCE_DIR}/event/*.cpp")

add_xsd_schema(xbe-msg "${CMAKE_SOURCE_DIR}/etc/xbe/schema/xbe-msg.xsd")
add_xsd_schema(xbe-instd "${CMAKE_SOURCE_DIR}/etc/xbe/schema/xbe-instd.xsd")
add_xsd_schema(jsdl "${CMAKE_SOURCE_DIR}/etc/xbe/schema/jsdl.xsd")
add_xsd_schema(jsdl-posix "${CMAKE_SOURCE_DIR}/etc/xbe/schema/jsdl-posix.xsd")
add_xsd_schema(dsig "${CMAKE_SOURCE_DIR}/etc/xbe/schema/dsig.xsd")
add_xsd_schema(xenc "${CMAKE_SOURCE_DIR}/etc/xbe/schema/xenc.xsd")

list(APPEND srcs "${CMAKE_CURRENT_SOURCE_DIR}/xbe-msg.cpp")
list(APPEND hdrs "${CMAKE_CURRENT_SOURCE_DIR}/xbe-msg.hpp")
list(APPEND srcs "${CMAKE_CURRENT_SOURCE_DIR}/xbe-instd.cpp")
list(APPEND hdrs "${CMAKE_CURRENT_SOURCE_DIR}/xbe-instd.hpp")
list(APPEND srcs "${CMAKE_CURRENT_SOURCE_DIR}/jsdl.cpp")
list(APPEND hdrs "${CMAKE_CURRENT_SOURCE_DIR}/jsdl.hpp")
list(APPEND srcs "${CMAKE_CURRENT_SOURCE_DIR}/jsdl-posix.cpp")
list(APPEND hdrs "${CMAKE_CURRENT_SOURCE_DIR}/jsdl-posix.hpp")
list(APPEND srcs "${CMAKE_CURRENT_SOURCE_DIR}/dsig.cpp")
list(APPEND hdrs "${CMAKE_CURRENT_SOURCE_DIR}/dsig.hpp")
list(APPEND srcs "${CMAKE_CURRENT_SOURCE_DIR}/xenc.cpp")
list(APPEND hdrs "${CMAKE_CURRENT_SOURCE_DIR}/xenc.hpp")

add_state_machine(XbeInstd srcs hdrs)
list(APPEND srcs "${CMAKE_CURRENT_SOURCE_DIR}/XbeInstd_sm.cpp")
list(APPEND hdrs "${CMAKE_CURRENT_SOURCE_DIR}/XbeInstd_sm.h")

list(REMOVE_DUPLICATES hdrs)
list(REMOVE_DUPLICATES srcs)

ADD_LIBRARY(xbe ${hdrs} ${srcs})

install(FILES ${hdrs} DESTINATION include/xbe)
install(TARGETS xbe
	ARCHIVE DESTINATION lib)

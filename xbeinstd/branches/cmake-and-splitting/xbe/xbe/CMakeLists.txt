file(GLOB hdrs "${CMAKE_CURRENT_SOURCE_DIR}/*.hpp")
file(GLOB srcs "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")

add_xsd_schema(xbe-msg "${CMAKE_SOURCE_DIR}/etc/xbe/schema/xbe-msg.xsd")
add_xsd_schema(jsdl "${CMAKE_SOURCE_DIR}/etc/xbe/schema/jsdl.xsd")
add_xsd_schema(jsdl-posix "${CMAKE_SOURCE_DIR}/etc/xbe/schema/jsdl-posix.xsd")
add_xsd_schema(dsig "${CMAKE_SOURCE_DIR}/etc/xbe/schema/dsig.xsd")
add_xsd_schema(xenc "${CMAKE_SOURCE_DIR}/etc/xbe/schema/xenc.xsd")

list(APPEND srcs "${CMAKE_CURRENT_SOURCE_DIR}/xbe-msg.cpp")
list(APPEND hdrs "${CMAKE_CURRENT_SOURCE_DIR}/xbe-msg.hpp")
list(APPEND srcs "${CMAKE_CURRENT_SOURCE_DIR}/jsdl.cpp")
list(APPEND hdrs "${CMAKE_CURRENT_SOURCE_DIR}/jsdl.hpp")
list(APPEND srcs "${CMAKE_CURRENT_SOURCE_DIR}/jsdl-posix.cpp")
list(APPEND hdrs "${CMAKE_CURRENT_SOURCE_DIR}/jsdl-posix.hpp")
list(APPEND srcs "${CMAKE_CURRENT_SOURCE_DIR}/dsig.cpp")
list(APPEND hdrs "${CMAKE_CURRENT_SOURCE_DIR}/dsig.hpp")
list(APPEND srcs "${CMAKE_CURRENT_SOURCE_DIR}/xenc.cpp")
list(APPEND hdrs "${CMAKE_CURRENT_SOURCE_DIR}/xenc.hpp")

list(REMOVE_DUPLICATES hdrs)
list(REMOVE_DUPLICATES srcs)

include_directories(${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${XSD_INCLUDE_DIR})
ADD_LIBRARY(xbe ${hdrs} ${srcs})

install(FILES ${hdrs} DESTINATION include/xbe)
install(TARGETS xbe
	ARCHIVE DESTINATION lib)

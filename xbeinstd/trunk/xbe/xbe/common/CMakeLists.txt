# -*- mode: cmake; -*-
file(GLOB srcs "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")
configure_file("${CMAKE_CURRENT_SOURCE_DIR}/config.h.in" "${CMAKE_CURRENT_BINARY_DIR}/xbe-config.h")
set(hdrs "common.hpp;logging.hpp;${CMAKE_CURRENT_BINARY_DIR}/xbe-config.h")
ADD_LIBRARY(xbe-common ${srcs})

install(FILES ${hdrs} DESTINATION include/xbe/common)
install(TARGETS xbe-common
	ARCHIVE DESTINATION lib)

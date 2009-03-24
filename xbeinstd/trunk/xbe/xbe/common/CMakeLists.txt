# -*- mode: cmake; -*-
file(GLOB srcs "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")
set(hdrs "common.hpp;logging.hpp")
ADD_LIBRARY(xbe-common ${srcs})

install(FILES ${hdrs} DESTINATION include/xbe/common)
install(TARGETS xbe-common
	ARCHIVE DESTINATION lib)

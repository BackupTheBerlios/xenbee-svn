file(GLOB hdrs "${CMAKE_CURRENT_SOURCE_DIR}/*.hpp")
file(GLOB srcs "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")

include_directories(${CMAKE_CURRENT_SOURCE_DIR})
ADD_LIBRARY(xbe ${hdrs} ${srcs})

install(FILES ${hdrs} DESTINATION include/xbe)
install(TARGETS xbe
	ARCHIVE DESTINATION lib)

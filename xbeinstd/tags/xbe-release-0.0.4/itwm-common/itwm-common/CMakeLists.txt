file(GLOB hdrs "${CMAKE_CURRENT_SOURCE_DIR}/*.hpp")
file(GLOB srcs "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")

include_directories(${CMAKE_CURRENT_SOURCE_DIR})
ADD_LIBRARY(itwm-common ${hdrs} ${srcs})

install(FILES ${hdrs} DESTINATION include/itwm-common)
install(TARGETS itwm-common 
	ARCHIVE DESTINATION lib)

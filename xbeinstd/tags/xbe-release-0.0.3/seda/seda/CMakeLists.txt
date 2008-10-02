file(GLOB hdrs "${CMAKE_CURRENT_SOURCE_DIR}/*.hpp")
file(GLOB srcs "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")

ADD_LIBRARY(seda ${hdrs} ${srcs})

install(FILES ${hdrs} DESTINATION include/seda)
install(TARGETS seda
	ARCHIVE DESTINATION lib)

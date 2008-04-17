file(GLOB hdrs "${CMAKE_CURRENT_SOURCE_DIR}/*.hpp")
file(GLOB srcs "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")

ADD_LIBRARY(mqs ${hdrs} ${srcs})

install(FILES ${hdrs} DESTINATION include/mqs)
install(TARGETS mqs
	ARCHIVE DESTINATION lib)

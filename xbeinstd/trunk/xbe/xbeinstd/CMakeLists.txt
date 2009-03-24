# -*- mode: cmake; -*-
file(GLOB hdrs "${CMAKE_CURRENT_SOURCE_DIR}/*.hpp")
file(GLOB srcs "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")

add_executable(xbeinstd ${srcs})

target_link_libraries(xbeinstd xbe-common xbe)

install(TARGETS xbeinstd RUNTIME DESTINATION bin)

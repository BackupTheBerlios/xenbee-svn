# -*- mode: cmake; -*-

set(xbeinstdtest_src main.cpp
   XbeInstdTest.hpp XbeInstdTest.cpp
)
include_directories(${CMAKE_CURRENT_BINARY_DIR})

configure_file(${CMAKE_SOURCE_DIR}/etc/log4j.properties ${CMAKE_CURRENT_BINARY_DIR}/log4j.properties COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/testsconfig.hpp.in ${CMAKE_CURRENT_BINARY_DIR}/testsconfig.hpp)
exec_program("${CMAKE_COMMAND}" ARGS "-E copy_directory \"${CMAKE_CURRENT_SOURCE_DIR}/resources\" \"${CMAKE_CURRENT_BINARY_DIR}/resources\"")

add_executable(xbeinstdtest ${xbeinstdtest_src})
add_test(xbeinstdtest ${CMAKE_CURRENT_BINARY_DIR}/xbeinstdtest)

target_link_libraries(xbeinstdtest xbe)

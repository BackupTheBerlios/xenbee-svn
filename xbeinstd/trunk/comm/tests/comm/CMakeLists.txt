# -*- mode: cmake; -*-

set(commtest_src main.cpp
    SimpleGlobalTest.cpp
)

include_directories(${CMAKE_CURRENT_BINARY_DIR})

configure_file(${CMAKE_CURRENT_SOURCE_DIR}/testsconfig.hpp.in ${CMAKE_CURRENT_BINARY_DIR}/testsconfig.hpp)

add_executable(commtestsuite ${commtest_src})
add_test(commtestsuite ${CMAKE_CURRENT_BINARY_DIR}/commtestsuite)
target_link_libraries(commtestsuite comm)

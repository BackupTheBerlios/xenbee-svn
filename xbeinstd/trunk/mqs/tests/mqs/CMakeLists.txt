# -*- mode: cmake; -*-

set(mqstest_src main.cpp
  MessageSequenceGeneratorTest.hpp MessageSequenceGeneratorTest.cpp 
  DestinationTest.hpp DestinationTest.cpp
  ChannelTest.hpp ChannelTest.cpp
)
include_directories(${CMAKE_CURRENT_BINARY_DIR})

configure_file(${CMAKE_SOURCE_DIR}/etc/log4j.properties ${CMAKE_CURRENT_BINARY_DIR}/log4j.properties COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/testsconfig.hpp.in ${CMAKE_CURRENT_BINARY_DIR}/testsconfig.hpp)

add_executable(mqstestsuite ${mqstest_src})
add_test(mqstestsuite ${CMAKE_CURRENT_BINARY_DIR}/mqstestsuite)
target_link_libraries(mqstestsuite mqs)

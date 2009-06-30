# -*- mode: cmake; -*-

set(sedaCommTest_src main.cpp
  EncoderTest.cpp
  ZMQConnectionTest.cpp
)

include_directories(${CMAKE_CURRENT_BINARY_DIR})

configure_file(${CMAKE_SOURCE_DIR}/etc/log4j.properties ${CMAKE_CURRENT_BINARY_DIR}/log4j.properties COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/testsconfig.hpp.in ${CMAKE_CURRENT_BINARY_DIR}/testsconfig.hpp)

add_executable(sedaCommTestsuite ${sedaCommTest_src})
add_test(sedaCommTestsuite ${CMAKE_CURRENT_BINARY_DIR}/sedaCommTestsuite)
target_link_libraries(sedaCommTestsuite seda sedaComm)

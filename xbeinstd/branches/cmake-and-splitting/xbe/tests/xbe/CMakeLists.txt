# -*- mode: cmake; -*-

set(xbetest_src main.cpp
   ChannelEventQueueAdapterTest.hpp ChannelEventQueueAdapterTest.cpp
   XMLEncodeDecodeTest.hpp XMLEncodeDecodeTest.cpp
#   XMLSecurityLibraryTest.hpp XMLSecurityLibraryTest.cpp
#   XMLSecurityTest.hpp XMLSecurityTest.cpp
)
include_directories(${CMAKE_CURRENT_BINARY_DIR})

configure_file(${CMAKE_SOURCE_DIR}/etc/log4j.properties ${CMAKE_CURRENT_BINARY_DIR}/log4j.properties COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/testsconfig.hpp.in ${CMAKE_CURRENT_BINARY_DIR}/testsconfig.hpp)

add_executable(xbetestsuite ${xbetest_src})
add_test(xbetestsuite ${CMAKE_CURRENT_BINARY_DIR}/xbetestsuite)
target_link_libraries(xbetestsuite xbe)

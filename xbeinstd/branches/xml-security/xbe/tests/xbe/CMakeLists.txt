# -*- mode: cmake; -*-

add_state_machine(PingPong)
list(APPEND srcs "${CMAKE_CURRENT_SOURCE_DIR}/PingPong_sm.cpp")
list(APPEND hdrs "${CMAKE_CURRENT_SOURCE_DIR}/PingPong_sm.h")

set(xbetest_src main.cpp
   ChannelEventQueueAdapterTest.hpp ChannelEventQueueAdapterTest.cpp
   ChannelAdapterStrategyTest.hpp ChannelAdapterStrategyTest.cpp
   XMLEncodeDecodeTest.hpp XMLEncodeDecodeTest.cpp
   PingPong_sm.h PingPong_sm.cpp
   PingPong.hpp PingPong.cpp
   PingPongTest.hpp PingPongTest.cpp
   XMLSecurityLibraryTest.hpp XMLSecurityLibraryTest.cpp
#   XMLSecurityTest.hpp XMLSecurityTest.cpp
)
include_directories(${CMAKE_CURRENT_BINARY_DIR})

configure_file(${CMAKE_SOURCE_DIR}/etc/log4j.properties ${CMAKE_CURRENT_BINARY_DIR}/log4j.properties COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/testsconfig.hpp.in ${CMAKE_CURRENT_BINARY_DIR}/testsconfig.hpp)

# copy ressource files to the build directory
exec_program("${CMAKE_COMMAND}" ARGS "-E copy_directory \"${CMAKE_CURRENT_SOURCE_DIR}/resources\" \"${CMAKE_CURRENT_BINARY_DIR}/resources\"")

add_executable(xbetestsuite ${xbetest_src})
add_test(xbetestsuite ${CMAKE_CURRENT_BINARY_DIR}/xbetestsuite)
target_link_libraries(xbetestsuite xbe)

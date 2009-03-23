# -*- mode: cmake; -*-

add_state_machine(PingPong)
list(APPEND srcs "${CMAKE_CURRENT_SOURCE_DIR}/PingPong_sm.cpp")
list(APPEND hdrs "${CMAKE_CURRENT_SOURCE_DIR}/PingPong_sm.h")

set(channeltest_src main.cpp
   ChannelAdapterStrategyTest.hpp ChannelAdapterStrategyTest.cpp
)

#set(xmlsecuritytest_src main.cpp
#   XMLSecurityLibraryTest.hpp XMLSecurityLibraryTest.cpp
#   XMLSecurityTest.hpp XMLSecurityTest.cpp
#)

set(xbemessage_encoding_src main.cpp
    MessageEncodingTest.hpp MessageEncodingTest.cpp
)

set(tasktest_src main.cpp TaskTest.hpp TaskTest.cpp)

#set(xmlendecodetest_src main.cpp
#    XMLEncodeDecodeTest.hpp XMLEncodeDecodeTest.cpp
#)

#set(xbetest_src main.cpp
#   PingPong_sm.h PingPong_sm.cpp
#   PingPong.hpp PingPong.cpp
#   PingPongTest.hpp PingPongTest.cpp
#)
include_directories(${CMAKE_CURRENT_BINARY_DIR})

configure_file(${CMAKE_SOURCE_DIR}/etc/log4j.properties ${CMAKE_CURRENT_BINARY_DIR}/log4j.properties COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/testsconfig.hpp.in ${CMAKE_CURRENT_BINARY_DIR}/testsconfig.hpp)

# copy ressource files to the build directory
exec_program("${CMAKE_COMMAND}" ARGS "-E copy_directory \"${CMAKE_CURRENT_SOURCE_DIR}/resources\" \"${CMAKE_CURRENT_BINARY_DIR}/resources\"")

add_executable(channeltest ${channeltest_src})
#add_executable(xmlsecuritytest ${xmlsecuritytest_src})
#add_executable(xmlendecodetest ${xmlendecodetest_src})
add_executable(msgencodingtest ${xbemessage_encoding_src})
#add_executable(xbetest ${xbetest_src})
#add_executable(xml-test-tool xml-test-tool.cpp)
add_executable(tasktest ${tasktest_src})

add_test(channeltest ${CMAKE_CURRENT_BINARY_DIR}/channeltest)
#add_test(xmlsecuritytest ${CMAKE_CURRENT_BINARY_DIR}/xmlsecuritytest)
#add_test(xmlendecodetest ${CMAKE_CURRENT_BINARY_DIR}/xmlendecodetest)
#add_test(xbetest ${CMAKE_CURRENT_BINARY_DIR}/xbetest)
add_test(msgencodingtest ${CMAKE_CURRENT_BINARY_DIR}/msgencodingtest)
add_test(tasktest ${CMAKE_CURRENT_BINARY_DIR}/tasktest)


target_link_libraries(channeltest xbe)
#target_link_libraries(xmlsecuritytest xbe)
#target_link_libraries(xmlendecodetest xbe)
target_link_libraries(msgencodingtest xbe)
#target_link_libraries(xbetest xbe)
#target_link_libraries(xml-test-tool xbe)
target_link_libraries(tasktest xbe)

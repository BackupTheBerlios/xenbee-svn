#include "ZMQConnectionTest.hpp"

#include <iostream>
#include <string>

#include <seda/comm/SedaMessage.hpp>
#include <seda/comm/ZMQConnection.hpp>

using namespace seda::comm::tests;

CPPUNIT_TEST_SUITE_REGISTRATION( ZMQConnectionTest );

ZMQConnectionTest::ZMQConnectionTest()
  : SEDA_INIT_LOGGER("tests.seda.comm.ZMQConnectionTest")
{}

void
ZMQConnectionTest::setUp() {
}

void
ZMQConnectionTest::tearDown() {
}

void
ZMQConnectionTest::testSendReceive() {
  seda::comm::ZMQConnection conn("localhost", "test", "*:5222", "*");
  try {
    conn.start();
  } catch (const std::exception &ex) {
    SEDA_LOG_ERROR("could not start the zmq-connection: " << ex.what());
    CPPUNIT_ASSERT_MESSAGE("zmq connection could not be started", false);
  } catch(...) {
    CPPUNIT_ASSERT_MESSAGE("zmq connection could not be started", false);
  }
  std::clog << "foo" << std::endl;
  seda::comm::SedaMessage msg1("test", "test", "foo");
  conn.send(msg1);
  seda::comm::SedaMessage msg2;
  conn.receive(msg2);
  CPPUNIT_ASSERT_MESSAGE("received payload differs from sent payload", msg1.payload() == msg2.payload());
}

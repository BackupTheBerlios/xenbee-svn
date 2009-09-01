#include "ZMQConnectionTest.hpp"

#include <iostream>
#include <string>
#include <stdexcept>
#include <signal.h>

#include <seda/comm/SedaMessage.hpp>
#include <seda/comm/ZMQConnection.hpp>

using namespace seda::comm::tests;

CPPUNIT_TEST_SUITE_REGISTRATION( ZMQConnectionTest );

void sighandler(int signal) {
  std::clog << "got signal: " << signal << std::endl;
}

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
  seda::comm::SedaMessage msg1("test", "test", "foo");
  conn.send(msg1);
  seda::comm::SedaMessage msg2;
  conn.receive(msg2);
  CPPUNIT_ASSERT_MESSAGE("received payload differs from sent payload", msg1.payload() == msg2.payload());
}

void
ZMQConnectionTest::testStartStop() {
  seda::comm::ZMQConnection conn("localhost", "test", "*:5222", "*");
  try {
    // FIXME: this segfaults for larger loop-counts! problem of libzmq!
    for (std::size_t i(0); i < 1; i++) {
      conn.start();

      seda::comm::SedaMessage msg1("test", "test", "foo");
      conn.send(msg1);
      seda::comm::SedaMessage msg2;
      conn.receive(msg2);
      CPPUNIT_ASSERT_MESSAGE("received payload differs from sent payload", msg1.payload() == msg2.payload());

      conn.stop();
    }
  } catch (const std::exception &ex) {
    SEDA_LOG_ERROR("could not start the zmq-connection: " << ex.what());
    CPPUNIT_ASSERT_MESSAGE("zmq connection could not be started", false);
  } catch(...) {
    CPPUNIT_ASSERT_MESSAGE("zmq connection could not be started", false);
  }
}


void
ZMQConnectionTest::testAbortException() {
  // register a signal handler for SIGABRT
  signal(SIGABRT, sighandler);
  // and throw an exception
  bool got_exception(false);
  try {
    throw std::runtime_error("42");
  } catch(const std::runtime_error &ex) {
    got_exception = true;
    const std::string expected("42");
    const std::string actual(ex.what());
    CPPUNIT_ASSERT_EQUAL(expected, actual);
  }
  CPPUNIT_ASSERT(got_exception);
}
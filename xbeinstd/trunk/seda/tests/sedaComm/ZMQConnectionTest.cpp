#include "ZMQConnectionTest.hpp"

#include <string>

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
  CPPUNIT_ASSERT_MESSAGE("implement me", false);
}

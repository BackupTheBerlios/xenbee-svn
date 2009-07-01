#ifndef SEDA_TESTS_COMM_ZMQCONN_HPP
#define SEDA_TESTS_COMM_ZMQCONN_HPP 1

#include <cppunit/extensions/HelperMacros.h>
#include <seda/logging.hpp>

namespace seda { namespace comm { namespace tests {
  class ZMQConnectionTest : public CppUnit::TestFixture {
    CPPUNIT_TEST_SUITE( seda::comm::tests::ZMQConnectionTest );
    CPPUNIT_TEST( testAbortException );
    CPPUNIT_TEST( testSendReceive );
    CPPUNIT_TEST( testStartStop );
    CPPUNIT_TEST_SUITE_END();

    private:

    public:
    ZMQConnectionTest();
    void setUp();
    void tearDown();

    protected:
    SEDA_DECLARE_LOGGER();
    void testSendReceive();
    void testStartStop();
    void testAbortException();
  };
}}}

#endif

#ifndef XBE_TESTS_MESSAGE_PING_PONG_TEST_HPP
#define XBE_TESTS_MESSAGE_PING_PONG_TEST_HPP 1

#include <cppunit/extensions/HelperMacros.h>
#include <xbe/common.hpp>

namespace xbe {
  namespace tests {
    class MessagePingPongTest : public CppUnit::TestFixture {
      CPPUNIT_TEST_SUITE( xbe::tests::MessagePingPongTest );
      //      CPPUNIT_TEST_EXCEPTION( testStart_illegal_URI_Throws, cms::CMSException );
      CPPUNIT_TEST( testSendPing );
      //      CPPUNIT_TEST_EXCEPTION( testStart_Timeout_Throws, cms::CMSException );
      CPPUNIT_TEST_SUITE_END();

    public:
      MessagePingPongTest();
      void setUp();
      void tearDown();

    protected:
      void testSendPing();
    private:
      DECLARE_LOGGER();
    };
  }
}

#endif // !XBE_TESTS_MESSAGE_PING_PONG_TEST_HPP

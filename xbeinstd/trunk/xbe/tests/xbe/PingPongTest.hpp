#ifndef XBE_TESTS_PING_PONG_TEST_HPP
#define XBE_TESTS_PING_PONG_TEST_HPP 1

#include <cppunit/extensions/HelperMacros.h>
#include <xbe/common.hpp>

namespace xbe {
  namespace tests {
    class PingPongTest : public CppUnit::TestFixture {
      CPPUNIT_TEST_SUITE( xbe::tests::PingPongTest );
      //      CPPUNIT_TEST_EXCEPTION( testStart_illegal_URI_Throws, cms::CMSException );
      CPPUNIT_TEST( testPingPong );
      CPPUNIT_TEST( testPingPongSigning );
      CPPUNIT_TEST( testPingPongComplete );
      //      CPPUNIT_TEST_EXCEPTION( testStart_Timeout_Throws, cms::CMSException );
      CPPUNIT_TEST_SUITE_END();

    public:
      PingPongTest();
      virtual ~PingPongTest();

      void setUp();
      void tearDown();

    protected:
      void testPingPong();
      void testPingPongSigning();
      void testPingPongComplete();
    private:
      XBE_DECLARE_LOGGER();
    };
  }
}

#endif // !XBE_TESTS_PING_PONG_TEST_HPP

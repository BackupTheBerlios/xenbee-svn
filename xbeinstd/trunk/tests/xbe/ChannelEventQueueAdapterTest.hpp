#ifndef XBE_TESTS_CHANNEL_EVENT_QUEUE_ADAPTER_TEST_HPP
#define XBE_TESTS_CHANNEL_EVENT_QUEUE_ADAPTER_TEST_HPP 1

#include <cppunit/extensions/HelperMacros.h>
#include <xbe/logging.hpp>

namespace xbe {
  namespace tests {
    class ChannelEventQueueAdapterTest : public CppUnit::TestFixture {
      CPPUNIT_TEST_SUITE( xbe::tests::ChannelEventQueueAdapterTest );
      //      CPPUNIT_TEST_EXCEPTION( testStart_illegal_URI_Throws, cms::CMSException );
      CPPUNIT_TEST( testSendViaChannelText );
      CPPUNIT_TEST( testSendViaChannelNoneText );
      CPPUNIT_TEST( testSendViaStageMessage );
      CPPUNIT_TEST( testSendViaStageNoneMessage );
      //      CPPUNIT_TEST( testSendReply );
      //      CPPUNIT_TEST_EXCEPTION( testStart_Timeout_Throws, cms::CMSException );
      CPPUNIT_TEST_SUITE_END();

    public:
      ChannelEventQueueAdapterTest();
      void setUp();
      void tearDown();

    protected:
      void testSendViaChannelText();
      void testSendViaChannelNoneText();

      void testSendViaStageMessage();
      void testSendViaStageNoneMessage();
    private:
      DECLARE_LOGGER();
    };
  }
}

#endif // !XBE_TESTS_CHANNEL_EVENT_QUEUE_ADAPTER_TEST_HPP

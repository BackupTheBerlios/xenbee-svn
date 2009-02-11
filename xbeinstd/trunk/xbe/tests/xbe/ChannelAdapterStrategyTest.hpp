#ifndef XBE_TESTS_CHANNEL_ADAPTER_STRATEGY_TEST_HPP
#define XBE_TESTS_CHANNEL_ADAPTER_STRATEGY_TEST_HPP 1

#include <cppunit/extensions/HelperMacros.h>
#include <xbe/common.hpp>

namespace xbe {
  namespace tests {
    class ChannelAdapterStrategyTest : public CppUnit::TestFixture {
      CPPUNIT_TEST_SUITE( xbe::tests::ChannelAdapterStrategyTest );
      CPPUNIT_TEST( testSendViaChannelText );
      CPPUNIT_TEST( testSendViaStageMessage );
      CPPUNIT_TEST( testSendViaStageNoneMessage );
      CPPUNIT_TEST_SUITE_END();

    public:
      ChannelAdapterStrategyTest();
      void setUp();
      void tearDown();

    protected:
      void testSendViaChannelText();

      void testSendViaStageMessage();
      void testSendViaStageNoneMessage();
    private:
      XBE_DECLARE_LOGGER();
    };
  }
}

#endif // !XBE_TESTS_CHANNEL_ADAPTER_STRATEGY_TEST_HPP

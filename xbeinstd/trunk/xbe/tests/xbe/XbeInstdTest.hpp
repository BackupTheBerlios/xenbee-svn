#ifndef XBE_TESTS_XBEINSTD_TEST_HPP
#define XBE_TESTS_XBEINSTD_TEST_HPP 1

#include <cppunit/extensions/HelperMacros.h>
#include <xbe/common.hpp>

#include <seda/Stage.hpp>
#include <seda/EventCountStrategy.hpp>
#include <seda/AccumulateStrategy.hpp>

namespace xbe {
  namespace tests {
    class XbeInstdTest : public CppUnit::TestFixture {
      CPPUNIT_TEST_SUITE( xbe::tests::XbeInstdTest );
      CPPUNIT_TEST( testLifeSign );
      CPPUNIT_TEST( testShutdown1 );
      CPPUNIT_TEST( testShutdown2 );
      CPPUNIT_TEST( testStatus1 );
      CPPUNIT_TEST( testTerminate1 );
      CPPUNIT_TEST( testTerminate2 );
      CPPUNIT_TEST( testExecute1 );
      CPPUNIT_TEST_SUITE_END();

    public:
      XbeInstdTest();
      void setUp();
      void tearDown();

    protected:
      void testLifeSign();
      void testShutdown1();
      void testShutdown2();
      void testStatus1();
      void testTerminate1();
      void testTerminate2();
      void testExecute1();
    private:
      XBE_DECLARE_LOGGER();
      seda::Stage::Ptr _discardStage;
      seda::Stage::Ptr _xbeInstdStage;
      seda::EventCountStrategy::Ptr _ecs;
      seda::AccumulateStrategy::Ptr _acc;
    };
  }
}

#endif // !XBE_TESTS_PING_PONG_TEST_HPP

#ifndef MQS_TESTS_DESTINATION_HPP
#define MQS_TESTS_DESTINATION_HPP 1

#include <cppunit/extensions/HelperMacros.h>
#include <mqs/Destination.hpp>

namespace mqs {
  namespace tests {
    class DestinationTest : public CppUnit::TestFixture {
      CPPUNIT_TEST_SUITE( mqs::tests::DestinationTest );
      CPPUNIT_TEST( testParsing );
      CPPUNIT_TEST( testProperties );
      CPPUNIT_TEST_SUITE_END();

    private:
      mqs::Destination *_dst;

    public:
      void setUp();
      void tearDown();

    protected:
      void testParsing();
      void testProperties();
    };
  }
}
  

#endif // !MQS_TESTS_DESTINATION_HPP

#ifndef XBE_TESTS_TASK_TEST_HPP
#define XBE_TESTS_TASK_TEST_HPP 1

#include <cppunit/extensions/HelperMacros.h>
#include <xbe/common.hpp>

namespace xbe {
  namespace tests {
    class TaskTest : public CppUnit::TestFixture {
      CPPUNIT_TEST_SUITE( xbe::tests::TaskTest );
      CPPUNIT_TEST( testRun );
      CPPUNIT_TEST( testNoExecutable );
      CPPUNIT_TEST( testSignal );
      CPPUNIT_TEST_SUITE_END();

    public:
      TaskTest();
      void setUp();
      void tearDown();

    protected:
      void testRun();
      void testNoExecutable();
      void testSignal();
    private:
      XBE_DECLARE_LOGGER();
    };
  }
}

#endif // !XBE_TESTS_TASK_TEST

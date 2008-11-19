#ifndef XBE_TESTS_MESSAGE_TRANSLATOR_TEST_HPP
#define XBE_TESTS_MESSAGE_TRANSLATOR_TEST_HPP 1

#include <cppunit/extensions/HelperMacros.h>
#include <xbe/common.hpp>

namespace xbe {
  namespace tests {
    class MessageTranslatorTest : public CppUnit::TestFixture {
      CPPUNIT_TEST_SUITE( xbe::tests::MessageTranslatorTest );
      CPPUNIT_TEST( testXMLExecute );
      CPPUNIT_TEST_SUITE_END();

    public:
      MessageTranslatorTest();
      void setUp();
      void tearDown();

    protected:
      void testXMLExecute();
    private:
      XBE_DECLARE_LOGGER();
    };
  }
}

#endif // !XBE_TESTS_MESSAGE_TRANSLATOR_TEST

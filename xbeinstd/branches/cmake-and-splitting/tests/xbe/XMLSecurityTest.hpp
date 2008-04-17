#ifndef XBE_TESTS_XML_SECURITY_TEST_HPP
#define XBE_TESTS_XML_SECURITY_TEST_HPP 1

#include <cppunit/extensions/HelperMacros.h>
#include <xbe/logging.hpp>

namespace xbe {
  namespace tests {
    class XMLSecurityTest : public CppUnit::TestFixture {
      CPPUNIT_TEST_SUITE( xbe::tests::XMLSecurityTest );
      //      CPPUNIT_TEST_EXCEPTION( testStart_illegal_URI_Throws, cms::CMSException );
      CPPUNIT_TEST( testSign );
      CPPUNIT_TEST( testValidate );
      CPPUNIT_TEST( testEncrypt );
      CPPUNIT_TEST( testDecrypt );
      //      CPPUNIT_TEST_EXCEPTION( testStart_Timeout_Throws, cms::CMSException );
      CPPUNIT_TEST_SUITE_END();

    public:
      XMLSecurityTest();
      void setUp();
      void tearDown();

    protected:
      void testSign();
      void testValidate();
      void testEncrypt();
      void testDecrypt();

    private:
      DECLARE_LOGGER();
    };
  }
}

#endif // !XBE_TESTS_XML_SECURITY_TEST_HPP

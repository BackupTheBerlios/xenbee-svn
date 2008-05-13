#ifndef XBE_TESTS_XML_ENCODE_DECODE_TEST_HPP
#define XBE_TESTS_XML_ENCODE_DECODE_TEST_HPP 1

#include <cppunit/extensions/HelperMacros.h>
#include <xbe/common.hpp>

namespace xbe {
  namespace tests {
    class XMLEncodeDecodeTest : public CppUnit::TestFixture {
      CPPUNIT_TEST_SUITE( xbe::tests::XMLEncodeDecodeTest );
      //      CPPUNIT_TEST_EXCEPTION( testStart_illegal_URI_Throws, cms::CMSException );
      CPPUNIT_TEST( testEncode );
      CPPUNIT_TEST( testDecode );
      CPPUNIT_TEST( testEncodeIllegal );
      CPPUNIT_TEST( testDecodeIllegal );
      CPPUNIT_TEST( testEnDecode );
      //      CPPUNIT_TEST_EXCEPTION( testStart_Timeout_Throws, cms::CMSException );
      CPPUNIT_TEST_SUITE_END();

    public:
      XMLEncodeDecodeTest();
      void setUp();
      void tearDown();

    protected:
      void testEncode();
      void testEncodeIllegal();
      void testDecode();
      void testDecodeIllegal();
      void testEnDecode();
    private:
      XBE_DECLARE_LOGGER();
    };
  }
}

#endif // !XBE_TESTS_XML_ENCODE_DECODE_TEST_HPP

#ifndef XBE_TESTS_MESSAGE_TRANSLATOR_TEST_HPP
#define XBE_TESTS_MESSAGE_TRANSLATOR_TEST_HPP 1

#include <cppunit/extensions/HelperMacros.h>
#include <xbe/common.hpp>

namespace xbe {
  namespace tests {
    class MessageTranslatorTest : public CppUnit::TestFixture {
      CPPUNIT_TEST_SUITE( xbe::tests::MessageTranslatorTest );
      CPPUNIT_TEST( testXMLExecute );
      CPPUNIT_TEST( testXMLExecuteAck );
      CPPUNIT_TEST( testExecuteAckEvent );
      CPPUNIT_TEST( testXMLShutdown );
      CPPUNIT_TEST( testShutdownEvent );
      CPPUNIT_TEST( testXMLShutdownAck );
      CPPUNIT_TEST( testShutdownAckEvent );
      CPPUNIT_TEST( testXMLFailed );
      CPPUNIT_TEST( testFailedEvent );
      CPPUNIT_TEST( testXMLStatusReq );
      CPPUNIT_TEST( testStatusReqEvent );
      CPPUNIT_TEST( testXMLLifeSign );
      CPPUNIT_TEST( testLifeSignEvent );
      CPPUNIT_TEST( testXMLStatus );
      CPPUNIT_TEST( testStatusEvent );
      CPPUNIT_TEST( testXMLFinished );
      CPPUNIT_TEST( testFinishedEvent );
      CPPUNIT_TEST( testXMLTerminateAck );
      CPPUNIT_TEST( testTerminateAckEvent );
      CPPUNIT_TEST_SUITE_END();

    public:
      MessageTranslatorTest();
      void setUp();
      void tearDown();

    protected:
      void testXMLExecute();
      void testXMLExecuteAck();
      void testExecuteAckEvent();
      void testXMLStatusReq();
      void testStatusReqEvent();
      void testXMLLifeSign();
      void testLifeSignEvent();
      void testXMLStatus();
      void testStatusEvent();
      void testXMLFinished();
      void testFinishedEvent();
      void testXMLTerminateAck();
      void testTerminateAckEvent();
      void testXMLShutdown();
      void testShutdownEvent();
      void testXMLShutdownAck();
      void testShutdownAckEvent();
      void testXMLFailed();
      void testFailedEvent();
      private:
      XBE_DECLARE_LOGGER();
    };
  }
}

#endif // !XBE_TESTS_MESSAGE_TRANSLATOR_TEST

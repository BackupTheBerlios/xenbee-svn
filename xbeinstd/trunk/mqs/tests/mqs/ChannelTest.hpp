#ifndef MQS_TESTS_CHANNEL_HPP
#define MQS_TESTS_CHANNEL_HPP 1

#include <cppunit/extensions/HelperMacros.h>
#include <tests/mqs/testsconfig.hpp>
#include <mqs/common.hpp>
#include <mqs/Channel.hpp>
#include <mqs/ExceptionListener.hpp>

namespace mqs {
    namespace tests {
        class ChannelTest : public CppUnit::TestFixture, public mqs::ExceptionListener {
            CPPUNIT_TEST_SUITE( mqs::tests::ChannelTest );
            CPPUNIT_TEST_EXCEPTION( testStart_illegal_URI_Throws, mqs::ChannelConnectionFailed );
            CPPUNIT_TEST( testSendReceiveSimple );
            CPPUNIT_TEST( testMessageId );
            CPPUNIT_TEST( testStartStopChannel );
            CPPUNIT_TEST( testSendReply );
            CPPUNIT_TEST( testSendReceiveLarge );
            CPPUNIT_TEST( testAddDelIncomingQueue );
            CPPUNIT_TEST( testMultipleSender );
            CPPUNIT_TEST( testStartNoQueueServer );
            //      CPPUNIT_TEST_EXCEPTION( testStart_Timeout_Throws, cms::CMSException );
#if defined(WITH_CONNECTIONLOST_TEST) && WITH_CONNECTIONLOST_TEST
            CPPUNIT_TEST( testConnectionLoss ); // this function should be last because the broker server needs to be shut down
#endif
          //CPPUNIT_TEST( testRestart );
            CPPUNIT_TEST_SUITE_END();

            public:
            ChannelTest();
            void setUp();
            void tearDown();

            void onException(const cms::CMSException &);
            void onException(const mqs::MQSException &);

            protected:
            void testStart_illegal_URI_Throws();
            void testStart_Timeout_Throws();
            void testSendReceiveSimple();
            void testSendReceiveLarge();
            void testMessageId();
            void testSendReply();
            void testStartNoQueueServer();
            void testStartStopChannel();
            void testAddDelIncomingQueue();
            void testConnectionLoss();
            void testMultipleSender();
            void testRestart();

            private:
            MQS_DECLARE_LOGGER();

            void doStart(const std::string &queue);
            void doStart(const char *queue);
            void doStart(const std::string &uri, const std::string &queue);

            mqs::Channel *_channel;
            bool _awaitingException;
            bool _exceptionArrived;
        };
    }
}


#endif // !MQS_TESTS_CHANNELTEST_HPP

#ifndef MQS_TESTS_CHANNEL_HPP
#define MQS_TESTS_CHANNEL_HPP 1

#include <cppunit/extensions/HelperMacros.h>
#include <cms/CMSException.h>
#include <mqs/common.hpp>
#include <mqs/Channel.hpp>

namespace mqs {
    namespace tests {
        class ChannelTest : public CppUnit::TestFixture, public cms::ExceptionListener {
            CPPUNIT_TEST_SUITE( mqs::tests::ChannelTest );
//            CPPUNIT_TEST_EXCEPTION( testStart_illegal_URI_Throws, cms::CMSException );
            CPPUNIT_TEST( testSendReceiveSimple );
            CPPUNIT_TEST( testMessageId );
            CPPUNIT_TEST( testStartStopChannel );
            CPPUNIT_TEST( testSendReply );
            CPPUNIT_TEST( testAddDelIncomingQueue );
            CPPUNIT_TEST( testMultipleSender );
//            CPPUNIT_TEST_EXCEPTION( testStartNoQueueServer_Throws, cms::CMSException );
            //      CPPUNIT_TEST_EXCEPTION( testStart_Timeout_Throws, cms::CMSException );
//            CPPUNIT_TEST( testConnectionLoss ); // this function should be last because the broker server needs to be shut down
            CPPUNIT_TEST_SUITE_END();

            public:
            ChannelTest();
            void setUp();
            void tearDown();

            void onException(const cms::CMSException &);

            protected:
            void testStart_illegal_URI_Throws();
            void testStart_Timeout_Throws();
            void testSendReceiveSimple();
            void testMessageId();
            void testSendReply();
            void testStartNoQueueServer_Throws();
            void testStartStopChannel();
            void testAddDelIncomingQueue();
            void testConnectionLoss();
            void testMultipleSender();

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

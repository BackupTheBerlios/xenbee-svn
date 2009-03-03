#ifndef XBE_TESTS_MESSAGE_ENCODING_TEST_HPP
#define XBE_TESTS_MESSAGE_ENCODING_TEST_HPP 1

#include <cppunit/extensions/HelperMacros.h>
#include <xbe/common.hpp>

#include <seda/Stage.hpp>
#include <seda/EventCountStrategy.hpp>
#include <seda/AccumulateStrategy.hpp>

namespace xbe {
    namespace tests {
        class MessageEncodingTest : public CppUnit::TestFixture {
            CPPUNIT_TEST_SUITE( xbe::tests::MessageEncodingTest );

            CPPUNIT_TEST( testError );
            CPPUNIT_TEST( testExecute );
            CPPUNIT_TEST( testExecuteAck );
            CPPUNIT_TEST( testExecuteNak );
            CPPUNIT_TEST( testStatusReq );
            CPPUNIT_TEST( testStatus );
            CPPUNIT_TEST( testFinished );
            CPPUNIT_TEST( testFinishedAck );
            CPPUNIT_TEST( testFailed );
            CPPUNIT_TEST( testFailedAck );
            CPPUNIT_TEST( testShutdown );
            CPPUNIT_TEST( testShutdownAck );
            CPPUNIT_TEST( testTerminate );
            CPPUNIT_TEST( testTerminateAck );
            CPPUNIT_TEST( testLifeSign );

            CPPUNIT_TEST_SUITE_END();

            public:
            MessageEncodingTest();
            virtual ~MessageEncodingTest();

            void setUp();
            void tearDown();

            protected:
            void testError ();
            void testExecute ();
            void testExecuteAck ();
            void testExecuteNak ();
            void testStatusReq ();
            void testStatus ();
            void testFinished ();
            void testFinishedAck ();
            void testFailed ();
            void testFailedAck ();
            void testShutdown ();
            void testShutdownAck ();
            void testTerminate ();
            void testTerminateAck ();
            void testLifeSign ();

            private:
            XBE_DECLARE_LOGGER();
            seda::Stage::Ptr _discard;
            seda::Stage::Ptr _encode;
            seda::Stage::Ptr _decode;
            seda::EventCountStrategy::Ptr _ecs;
            seda::AccumulateStrategy::Ptr _acc;
        };
    }
}

#endif // !XBE_TESTS_PING_PONG_TEST_HPP

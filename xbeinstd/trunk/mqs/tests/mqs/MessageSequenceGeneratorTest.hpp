#ifndef MQS_TESTS_MSGSEQUENCE_HPP
#define MQS_TESTS_MSGSEQUENCE_HPP 1

#include <cppunit/extensions/HelperMacros.h>
#include <mqs/common.hpp>

namespace mqs {
    namespace tests {
        class MessageSequenceGeneratorTest : public CppUnit::TestFixture {
            CPPUNIT_TEST_SUITE( mqs::tests::MessageSequenceGeneratorTest );
            CPPUNIT_TEST( testUniqueness );
            CPPUNIT_TEST_SUITE_END();

            public:
            MessageSequenceGeneratorTest();

            void setUp();
            void tearDown();

            protected:
            void testUniqueness();

            private:
            MQS_DECLARE_LOGGER();
        };
    }
}


#endif // !MQS_TESTS_CHANNELTEST_HPP

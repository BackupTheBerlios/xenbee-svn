#ifndef MQS_TESTS_PROPERTIES_HPP
#define MQS_TESTS_PROPERTIES_HPP 1

#include <cppunit/extensions/HelperMacros.h>
#include <mqs/Properties.hpp>

namespace mqs {
    namespace tests {
        class PropertiesTest : public CppUnit::TestFixture {
            CPPUNIT_TEST_SUITE( mqs::tests::PropertiesTest );
            CPPUNIT_TEST( testStore );
            CPPUNIT_TEST( testStoreInt );
            CPPUNIT_TEST( testStoreBool );
            CPPUNIT_TEST( testInvalidConversion );
            CPPUNIT_TEST( testLookupFailed );
            CPPUNIT_TEST_SUITE_END();

            public:
            void setUp();
            void tearDown();

            protected:
            void testStore();
            void testStoreInt();
            void testStoreBool();
            void testInvalidConversion();
            void testLookupFailed();

            mqs::Properties _props;
        };
    }
}


#endif // !MQS_TESTS_DESTINATION_HPP

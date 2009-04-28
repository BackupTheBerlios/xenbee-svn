#include <comm/Global.hpp>
#include <comm/SimpleGlobal.hpp>

#include <cppunit/extensions/HelperMacros.h>

namespace seda {
namespace comm {
namespace tests {
    class SimpleGlobalTest : public CppUnit::TestFixture {
        CPPUNIT_TEST_SUITE( seda::comm::tests::SimpleGlobalTest );
        CPPUNIT_TEST( testPut );
        CPPUNIT_TEST( testGet );
        CPPUNIT_TEST_SUITE_END();

    private:
    public:
        void setUp() {
            Global::setInstance(new SimpleGlobal("foo")); 
        }
        void tearDown() {
            Global::setInstance(0); 
        }

    protected:
        void testPut() {
            Global::put("foo", "bar");
            Global::get("foo");
        }

        void testGet() {
        }
    };

    CPPUNIT_TEST_SUITE_REGISTRATION( SimpleGlobalTest );
}}}

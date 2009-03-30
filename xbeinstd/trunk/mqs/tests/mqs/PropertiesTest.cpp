#include <iostream>
#include <string>

#include "PropertiesTest.hpp"

using namespace mqs::tests;

CPPUNIT_TEST_SUITE_REGISTRATION( PropertiesTest );

void PropertiesTest::setUp() {
    _props.clear();
}

void PropertiesTest::tearDown() {
    _props.clear();
}

void PropertiesTest::testStore() {
    CPPUNIT_ASSERT(_props.empty());
    _props.put("foo", "bar");
    CPPUNIT_ASSERT_EQUAL(std::string("bar"), _props.get("foo"));
    _props.del("foo");
    CPPUNIT_ASSERT(_props.empty());
}

void PropertiesTest::testStoreInt() {
    _props.put("foo", 1);
    CPPUNIT_ASSERT_EQUAL(1, _props.get<int>("foo"));
}

void PropertiesTest::testStoreBool() {
    _props.put("foo", true);
    CPPUNIT_ASSERT_EQUAL(true, _props.get<bool>("foo"));
}

void PropertiesTest::testInvalidConversion() {
    _props.put("foo", "foo");
    try {
        bool b(_props.get<bool>("foo"));
        CPPUNIT_ASSERT(b != true && b == true); // assert a contradiction just to make use of 'b'
    } catch (const mqs::PropertyConversionFailed &) {
        // pass
    }
}

void PropertiesTest::testLookupFailed() {
    CPPUNIT_ASSERT(_props.empty());
    try {
        _props.get("foo");
        CPPUNIT_ASSERT(false);
    } catch (const mqs::PropertyLookupFailed&) {
        // pass
    }
}

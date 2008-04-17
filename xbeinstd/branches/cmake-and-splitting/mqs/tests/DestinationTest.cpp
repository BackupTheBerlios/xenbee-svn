#include <iostream>
#include <string>

#include "DestinationTest.hpp"

using namespace mqs::tests;

CPPUNIT_TEST_SUITE_REGISTRATION( DestinationTest );

void DestinationTest::setUp() {
  _dst = new mqs::Destination("foo.bar?timeToLive=1&type=queue");
}

void DestinationTest::tearDown() {
  delete _dst;
}

void DestinationTest::testParsing() {
  CPPUNIT_ASSERT_EQUAL(std::string("foo.bar"), _dst->name());
  CPPUNIT_ASSERT_EQUAL(false, _dst->isTopic());
}

void DestinationTest::testProperties() {
  CPPUNIT_ASSERT_EQUAL(std::string("foo.bar"), _dst->name());
  CPPUNIT_ASSERT_EQUAL(false, _dst->hasProperty("prop1"));
  CPPUNIT_ASSERT_EQUAL(2, _dst->getIntProperty("prop1", 2));
  CPPUNIT_ASSERT_EQUAL(1, _dst->getIntProperty("timeToLive"));
}

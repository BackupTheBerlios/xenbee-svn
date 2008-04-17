#include "testsconfig.hpp"
#include "XMLEncodeDecodeTest.hpp"

#include <string>

#include <seda/Stage.hpp>
#include <seda/EventQueue.hpp>
#include <seda/IEvent.hpp>
#include <seda/ForwardStrategy.hpp>
#include <seda/EventCountStrategy.hpp>
#include <seda/DiscardStrategy.hpp>
#include <seda/LoggingStrategy.hpp>

#include <xbe/XbeLibUtils.hpp>
#include <xbe/MessageEvent.hpp>
#include <xbe/XMLMessageEvent.hpp>
#include <xbe/XMLSerializeStrategy.hpp>
#include <xbe/XMLDeserializeStrategy.hpp>

#include <xbe/xbe-schema.hpp>

using namespace xbe::tests;

CPPUNIT_TEST_SUITE_REGISTRATION( XMLEncodeDecodeTest );

XMLEncodeDecodeTest::XMLEncodeDecodeTest()
  : INIT_LOGGER("tests.xbe.xml-endecode")
{}

void
XMLEncodeDecodeTest::setUp() {
  XbeLibUtils::initialise();
}

void
XMLEncodeDecodeTest::tearDown() {
  XbeLibUtils::terminate();
}

void
XMLEncodeDecodeTest::testEncode() {
  seda::Strategy::Ptr discard(new seda::DiscardStrategy());
  seda::EventCountStrategy *ecs = new seda::EventCountStrategy(discard);
  discard = seda::Strategy::Ptr(ecs);
  discard = seda::Strategy::Ptr(new seda::LoggingStrategy(discard));
  seda::Stage::Ptr final(new seda::Stage("final", discard));

  seda::Strategy::Ptr fwd(new seda::ForwardStrategy(final));
  fwd = seda::Strategy::Ptr(new xbe::XMLSerializeStrategy(fwd));
  seda::Stage::Ptr start(new seda::Stage("final", fwd));

  start->start();
  final->start();

  LOG_DEBUG("sending XML message");
  xbexsd::header_t hdr("tests.xbe.foo.bar", "tests.xbe.foo.bar");
  xbexsd::body_t body;
  xbexsd::error_t error(xbexsd::ErrorCode(xbexsd::ErrorCode::ENOERROR));
  body.error().set(error);
  seda::IEvent::Ptr xmlMsg(new xbe::XMLMessageEvent(xbexsd::message_t(hdr,body)));

  start->send(xmlMsg);
  ecs->wait(1, 1000);

  CPPUNIT_ASSERT(final->queue()->empty());
  CPPUNIT_ASSERT(ecs->count() == 1);

  final->stop();
}

void
XMLEncodeDecodeTest::testEncodeIllegal() {
  
}

void
XMLEncodeDecodeTest::testDecode() {

}

void
XMLEncodeDecodeTest::testDecodeIllegal() {
}

void
XMLEncodeDecodeTest::testEnDecode() {

}

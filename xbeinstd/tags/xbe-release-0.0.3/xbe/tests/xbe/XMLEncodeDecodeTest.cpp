#include "testsconfig.hpp"
#include "XMLEncodeDecodeTest.hpp"

#include <string>

#include <seda/Stage.hpp>
#include <seda/EventQueue.hpp>
#include <seda/IEvent.hpp>
#include <seda/StageRegistry.hpp>
#include <seda/ForwardStrategy.hpp>
#include <seda/EventCountStrategy.hpp>
#include <seda/DiscardStrategy.hpp>
#include <seda/LoggingStrategy.hpp>

#include <xbe/XbeLibUtils.hpp>
#include <xbe/MessageEvent.hpp>
#include <xbe/XMLMessageEvent.hpp>
#include <xbe/XMLSerializeStrategy.hpp>
#include <xbe/XMLDeserializeStrategy.hpp>

#include <xbe/xbe-msg.hpp>

using namespace xbe::tests;

CPPUNIT_TEST_SUITE_REGISTRATION( XMLEncodeDecodeTest );

XMLEncodeDecodeTest::XMLEncodeDecodeTest()
  : XBE_INIT_LOGGER("tests.xbe.xml-endecode")
{}

void
XMLEncodeDecodeTest::setUp() {
  XbeLibUtils::initialise();
}

void
XMLEncodeDecodeTest::tearDown() {
  seda::StageRegistry::instance().clear();
  XbeLibUtils::terminate();
}

void
XMLEncodeDecodeTest::testEncode() {
  seda::Strategy::Ptr discard(new seda::DiscardStrategy());
  seda::EventCountStrategy *ecs = new seda::EventCountStrategy(discard);
  discard = seda::Strategy::Ptr(ecs);
  discard = seda::Strategy::Ptr(new seda::LoggingStrategy(discard));
  seda::Stage::Ptr final(new seda::Stage("final", discard));

  seda::Strategy::Ptr fwd(new seda::ForwardStrategy("final"));
  fwd = seda::Strategy::Ptr(new xbe::XMLSerializeStrategy(fwd));
  seda::Stage::Ptr start(new seda::Stage("final", fwd));

  seda::StageRegistry::instance().insert(final);

  start->start();
  final->start();

  XBE_LOG_DEBUG("sending XML message");
  xbemsg::header_t hdr("tests.xbe.foo.bar", "tests.xbe.foo.bar");
  xbemsg::body_t body;
  seda::IEvent::Ptr xmlMsg(new xbe::XMLMessageEvent(xbemsg::message_t(hdr,body)));

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

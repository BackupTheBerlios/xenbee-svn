#include "testsconfig.hpp"
#include "ChannelAdapterStrategyTest.hpp"

#include <string>

#include <xbe/common.hpp>
#include <xbe/ChannelAdapterStrategy.hpp>
#include <xbe/event/MessageEvent.hpp>

#include <seda/Stage.hpp>
#include <seda/EventQueue.hpp>
#include <seda/IEvent.hpp>
#include <seda/StringEvent.hpp>
#include <seda/EventCountStrategy.hpp>
#include <seda/DiscardStrategy.hpp>
#include <seda/LoggingStrategy.hpp>

using namespace xbe::tests;

CPPUNIT_TEST_SUITE_REGISTRATION( ChannelAdapterStrategyTest );

ChannelAdapterStrategyTest::ChannelAdapterStrategyTest()
  : XBE_INIT_LOGGER("tests.xbe.channeladapter")
{}

void
ChannelAdapterStrategyTest::setUp() {}

void
ChannelAdapterStrategyTest::tearDown() {}

void
ChannelAdapterStrategyTest::testSendViaChannelText() {
  mqs::Channel::Ptr channel(new mqs::Channel(mqs::BrokerURI(TEST_BROKER_URI),
					     mqs::Destination("tests.xbe.queue?type=queue")));
  seda::Strategy::Ptr discard(new seda::DiscardStrategy());
  seda::EventCountStrategy::Ptr ecs(new seda::EventCountStrategy(discard));
  discard = seda::Strategy::Ptr(ecs);
  discard = seda::Strategy::Ptr(new ::xbe::ChannelAdapterStrategy("tests.xbe.channeladapter", discard, channel));
  seda::Stage::Ptr stage(new seda::Stage("net", discard));

  channel->start();
  channel->flushMessages();
  stage->start();
  
  channel->send("testSendViaChannelText"); // message will be consumed by discard strategy

  XBE_LOG_INFO("waiting at most 2s for message arival");
  ecs->wait(1, 2000);

  CPPUNIT_ASSERT(stage->queue()->empty());
  CPPUNIT_ASSERT(ecs->count() == 1);

  stage->stop();
  channel->stop();
}

void
ChannelAdapterStrategyTest::testSendViaChannelNoneText() {
  mqs::Channel::Ptr channel(new mqs::Channel(mqs::BrokerURI(TEST_BROKER_URI),
					     mqs::Destination("tests.xbe.queue?type=queue")));
  seda::Strategy::Ptr discard(new seda::DiscardStrategy());
  seda::EventCountStrategy::Ptr ecs(new seda::EventCountStrategy(discard));
  discard = seda::Strategy::Ptr(ecs);
  discard = seda::Strategy::Ptr(new ::xbe::ChannelAdapterStrategy("tests.xbe.channeladapter", discard, channel));
  seda::Stage::Ptr stage(new seda::Stage("net", discard));

  channel->start();
  channel->flushMessages();
  stage->start();

  cms::BytesMessage *bmsg = channel->createBytesMessage();
  channel->send(bmsg);
  delete bmsg;

  XBE_LOG_INFO("waiting at most 1s for message arival");
  ecs->wait(1, 1000);

  CPPUNIT_ASSERT(stage->queue()->empty());
  CPPUNIT_ASSERT(ecs->count() == 0); // message shall not be delivered

  stage->stop();
  channel->stop();
}

void
ChannelAdapterStrategyTest::testSendViaStageMessage() {
  mqs::Channel::Ptr channel(new mqs::Channel(mqs::BrokerURI(TEST_BROKER_URI),
					     mqs::Destination("tests.xbe.queue?type=queue")));
  seda::Strategy::Ptr discard(new seda::DiscardStrategy());
  seda::EventCountStrategy::Ptr ecs(new seda::EventCountStrategy(discard));
  discard = seda::Strategy::Ptr(ecs);
  discard = seda::Strategy::Ptr(new ::xbe::ChannelAdapterStrategy("tests.xbe.channeladapter", discard, channel));
  seda::Stage::Ptr stage(new seda::Stage("net", discard));

  channel->start();
  channel->flushMessages();
  stage->start();
  
  stage->send(seda::IEvent::Ptr(new xbe::event::MessageEvent("testSendViaStageMessage")));

  XBE_LOG_INFO("waiting at most 2s for message arival");
  ecs->wait(1, 2000);

  CPPUNIT_ASSERT(stage->queue()->empty());
  CPPUNIT_ASSERT(ecs->count() == 1);

  stage->stop();
  channel->stop();
}

void
ChannelAdapterStrategyTest::testSendViaStageNoneMessage() {
  mqs::Channel::Ptr channel(new mqs::Channel(mqs::BrokerURI(TEST_BROKER_URI),
					     mqs::Destination("tests.xbe.queue?type=queue")));
  seda::Strategy::Ptr discard(new seda::DiscardStrategy());
  seda::EventCountStrategy::Ptr ecs(new seda::EventCountStrategy(discard));
  discard = seda::Strategy::Ptr(new ::xbe::ChannelAdapterStrategy("tests.xbe.channeladapter", ecs, channel));
  seda::Stage::Ptr stage(new seda::Stage("net", discard));

  channel->start();
  channel->flushMessages();
  stage->start();
  
  stage->send(seda::IEvent::Ptr(new seda::StringEvent("testSendViaStageNoneMessage")));

  ecs->waitNoneZero(500); // give time to send a message (should not happen)

  CPPUNIT_ASSERT(stage->queue()->empty());
  CPPUNIT_ASSERT(ecs->count() == 0);

  stage->stop();
  channel->stop();
}

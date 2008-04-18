#include "testsconfig.hpp"
#include "ChannelEventQueueAdapterTest.hpp"

#include <string>

#include <xbe/common.hpp>
#include <xbe/ChannelEventQueueAdapter.hpp>
#include <xbe/MessageEvent.hpp>

#include <seda/Stage.hpp>
#include <seda/EventQueue.hpp>
#include <seda/IEvent.hpp>
#include <seda/StringEvent.hpp>
#include <seda/EventCountStrategy.hpp>
#include <seda/DiscardStrategy.hpp>
#include <seda/LoggingStrategy.hpp>

using namespace xbe::tests;

CPPUNIT_TEST_SUITE_REGISTRATION( ChannelEventQueueAdapterTest );

ChannelEventQueueAdapterTest::ChannelEventQueueAdapterTest()
  : INIT_LOGGER("tests.xbe.channeladapter")
{}

void
ChannelEventQueueAdapterTest::setUp() {}

void
ChannelEventQueueAdapterTest::tearDown() {}

void
ChannelEventQueueAdapterTest::testSendViaChannelText() {
  mqs::Channel::Ptr channel(new mqs::Channel(mqs::BrokerURI(TEST_BROKER_URI),
					     mqs::Destination("tests.xbe.queue?type=queue")));
  seda::IEventQueue::Ptr queue(new xbe::ChannelEventQueueAdapter(channel));
  seda::Strategy::Ptr discard(new seda::DiscardStrategy());
  seda::EventCountStrategy::Ptr ecs(new seda::EventCountStrategy(discard));
  discard = seda::Strategy::Ptr(ecs);
  
  seda::Stage::Ptr stage(new seda::Stage("net", queue, discard));

  channel->start();
  stage->start();
  
  channel->send("testSendViaChannelText"); // message will be consumed by discard strategy

  LOG_INFO("waiting at most 2s for message arival");
  ecs->wait(1, 2000);

  CPPUNIT_ASSERT(stage->queue()->empty());
  CPPUNIT_ASSERT(ecs->count() == 1);

  stage->stop();
  channel->stop();
}

void
ChannelEventQueueAdapterTest::testSendViaChannelNoneText() {
  mqs::Channel::Ptr channel(new mqs::Channel(mqs::BrokerURI(TEST_BROKER_URI),
					     mqs::Destination("tests.xbe.queue?type=queue")));
  seda::IEventQueue::Ptr queue(new xbe::ChannelEventQueueAdapter(channel));
  seda::Strategy::Ptr discard(new seda::DiscardStrategy());
  seda::EventCountStrategy::Ptr ecs(new seda::EventCountStrategy(discard));
  discard = seda::Strategy::Ptr(ecs);
  
  seda::Stage::Ptr stage(new seda::Stage("net", queue, discard));

  channel->start();
  stage->start();

  cms::BytesMessage *bmsg = channel->createBytesMessage();
  channel->send(bmsg);
  delete bmsg;

  LOG_INFO("waiting at most 1s for message arival");
  ecs->wait(1, 1000);

  CPPUNIT_ASSERT(stage->queue()->empty());
  CPPUNIT_ASSERT(ecs->count() == 0); // message shall not be delivered

  stage->stop();
  channel->stop();
  //  CPPUNIT_ASSERT_MESSAGE("test not implemented", false);
}

void
ChannelEventQueueAdapterTest::testSendViaStageMessage() {
  mqs::Channel::Ptr channel(new mqs::Channel(mqs::BrokerURI(TEST_BROKER_URI),
					     mqs::Destination("tests.xbe.queue?type=queue")));
  seda::IEventQueue::Ptr queue(new xbe::ChannelEventQueueAdapter(channel));

  seda::Strategy::Ptr discard(new seda::DiscardStrategy());
  seda::EventCountStrategy::Ptr ecs(new seda::EventCountStrategy(discard));
  discard = seda::Strategy::Ptr(ecs);
  
  seda::Stage::Ptr stage(new seda::Stage("net", queue, discard));

  channel->start();
  stage->start();
  
  stage->send(seda::IEvent::Ptr(new xbe::MessageEvent("testSendViaStageMessage")));

  LOG_INFO("waiting at most 2s for message arival");
  ecs->wait(1, 2000);

  CPPUNIT_ASSERT(stage->queue()->empty());
  CPPUNIT_ASSERT(ecs->count() == 1);

  stage->stop();
  channel->stop();
}

void
ChannelEventQueueAdapterTest::testSendViaStageNoneMessage() {
  mqs::Channel::Ptr channel(new mqs::Channel(mqs::BrokerURI(TEST_BROKER_URI),
					     mqs::Destination("tests.xbe.queue?type=queue")));
  seda::IEventQueue::Ptr queue(new xbe::ChannelEventQueueAdapter(channel));

  seda::Strategy::Ptr discard(new seda::DiscardStrategy());
  seda::EventCountStrategy::Ptr ecs(new seda::EventCountStrategy(discard));
  discard = seda::Strategy::Ptr(ecs);

  seda::Stage::Ptr stage(new seda::Stage("net", queue, discard));

  channel->start();
  stage->start();
  
  stage->send(seda::IEvent::Ptr(new seda::StringEvent("testSendViaStageNoneMessage")));

  ecs->waitNoneZero(500); // give time to send a message (should not happen)

  CPPUNIT_ASSERT(stage->queue()->empty());
  CPPUNIT_ASSERT(ecs->count() == 0);

  stage->stop();
  channel->stop();
}

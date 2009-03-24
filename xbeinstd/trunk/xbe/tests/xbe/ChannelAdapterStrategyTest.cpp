#include "testsconfig.hpp"
#include "ChannelAdapterStrategyTest.hpp"

#include <string>

#include <xbe/common/common.hpp>
#include <xbe/ChannelAdapterStrategy.hpp>
#include <xbe/event/MessageEvent.hpp>

#include <seda/Stage.hpp>
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
ChannelAdapterStrategyTest::testConnectionFailed() {
    mqs::Channel::Ptr channel(new mqs::Channel(mqs::BrokerURI("tcp://127.0.0.1:12345"), mqs::Destination("tests.xbe.queue")));

    seda::Strategy::Ptr discard(new seda::DiscardStrategy());
    seda::EventCountStrategy::Ptr ecs(new seda::EventCountStrategy(discard));
    discard = seda::Strategy::Ptr(ecs);
    discard = seda::Strategy::Ptr(new ::xbe::ChannelAdapterStrategy("tests.xbe.channeladapter", discard, channel));
    seda::Stage::Ptr stage(new seda::Stage("net", discard));

    XBE_LOG_DEBUG("starting stage");
    try {
        stage->start();
        CPPUNIT_ASSERT_MESSAGE(false, "channel starting should fail");
    } catch (const cms::CMSException &e) {

    }

    // try to send a message
    try {
        channel->send(mqs::Message("testConnectionFailed", "tests.xbe.queue", "tests.xbe.queue"));
        CPPUNIT_ASSERT_MESSAGE(false, "sending message over a not started channel");
    } catch (const mqs::ChannelNotStarted &cns) {
        // ok, pass
    }

    XBE_LOG_DEBUG("waiting for a message to arrive");
    ecs->wait(1, 1000);

    stage->stop();
}

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

    channel->send(mqs::Message("testSendViaChannelText", "test.xbe.queue", "tests.xbe.queue")); // message will be consumed by discard strategy

    XBE_LOG_INFO("waiting at most 2s for message arival");
    ecs->wait(1, 2000);

    CPPUNIT_ASSERT(stage->empty());
    CPPUNIT_ASSERT(ecs->count() == 1);

    stage->stop();
    channel->stop();
}

/*
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

   CPPUNIT_ASSERT(stage->empty());
   CPPUNIT_ASSERT(ecs->count() == 0); // message shall not be delivered

   stage->stop();
   channel->stop();
   }
   */

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

    stage->send(seda::IEvent::Ptr(new xbe::event::MessageEvent("testSendViaStageMessage", "tests.xbe.queue", "tests.xbe.queue")));

    XBE_LOG_INFO("waiting at most 2s for message arival");
    ecs->wait(1, 2000);

    CPPUNIT_ASSERT(stage->empty());
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

    stage->send(seda::IEvent::Ptr(new seda::StringEvent("non-message-event")));

    ecs->waitNoneZero(500); // give time to send a message (should not happen)

    CPPUNIT_ASSERT(stage->empty());
    CPPUNIT_ASSERT(ecs->count() == 0);

    stage->stop();
    channel->stop();
}

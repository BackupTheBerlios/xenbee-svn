#include <string>

#include <xbe/common.hpp>
#include <xbe/XbeLibUtils.hpp>
#include <xbe/ChannelAdapterStrategy.hpp>
#include <xbe/XMLSerializeStrategy.hpp>
#include <xbe/XMLDeserializeStrategy.hpp>
#include <xbe/XMLMessageEvent.hpp>

#include <seda/Stage.hpp>
#include <seda/IEvent.hpp>
#include <seda/StringEvent.hpp>
#include <seda/EventCountStrategy.hpp>
#include <seda/StageRegistry.hpp>
#include <seda/DiscardStrategy.hpp>
#include <seda/ForwardStrategy.hpp>
#include <seda/LoggingStrategy.hpp>

#include "testsconfig.hpp"
#include "PingPong.hpp"
#include "PingPongTest.hpp"

using namespace xbe::tests;

CPPUNIT_TEST_SUITE_REGISTRATION( PingPongTest );

PingPongTest::PingPongTest()
    : XBE_INIT_LOGGER("tests.xbe.pingpong")
{}

void
PingPongTest::setUp() {
  XbeLibUtils::initialise();
}

void
PingPongTest::tearDown() {
    seda::StageRegistry::instance().clear();
    XbeLibUtils::terminate();
}

void PingPongTest::testPingPong() {
    /*
                  xml                   ChannelStub
FSM <- PingClient --> XMLSerializer ---> Forwarder --> XMLDeserializer ---> PongClient --> FSM
       ^                                                                             |
       |                                ChannelStub                                  |
       +------------ XMLDeserializer <-- Forwarder <--- XMLSerializer <--------------+
    */

    const std::size_t numMsgs(5);
    
    
    /*
     * Ping part
     *
     */

    /* PingClient stage */
    ::tests::xbe::PingPong::Ptr pingClient(new ::tests::xbe::PingPong("tests.xbe.pingpong.ping.stage.strategy",
                                                                      "tests.xbe.ping.stage.xml-serialize", // next stage
                                                                      "tests.xbe.pingpong.pong", // messages go to
                                                                      "tests.xbe.pingpong.ping", // messages come from
                                                                      numMsgs, // number of messages to send
                                                                      true // perform the initial send
                                                                      ));
    seda::Stage::Ptr pingClientStage(new seda::Stage("tests.xbe.pingpong.ping.stage", pingClient));
    seda::StageRegistry::instance().insert(pingClientStage);
    
    /* XML Serializer stage */
    seda::Strategy::Ptr pingXmlSerializer(new seda::ForwardStrategy("tests.xbe.ping.net"));
    pingXmlSerializer = seda::Strategy::Ptr(new seda::LoggingStrategy(pingXmlSerializer));
    pingXmlSerializer = seda::Strategy::Ptr(new ::xbe::XMLSerializeStrategy(pingXmlSerializer));
    seda::Stage::Ptr pingXmlSerializeStage(new seda::Stage("tests.xbe.ping.stage.xml-serialize", pingXmlSerializer));
    seda::StageRegistry::instance().insert(pingXmlSerializeStage);
    
    /* ChannelStub */
    seda::Strategy::Ptr pingNetStub(new seda::ForwardStrategy("tests.xbe.pong.stage.xml-deserialize"));
    seda::EventCountStrategy::Ptr ecsPingNetStub(new seda::EventCountStrategy(pingNetStub));
    pingNetStub = ecsPingNetStub;
    seda::Stage::Ptr pingNetStage(new seda::Stage("tests.xbe.ping.net", pingNetStub));
    seda::StageRegistry::instance().insert(pingNetStage);
    
    /* XML De-Serializer stage */
    seda::Strategy::Ptr pingXmlDeSerializer(new seda::ForwardStrategy("tests.xbe.pingpong.ping.stage"));
    pingXmlDeSerializer = seda::Strategy::Ptr(new ::xbe::XMLDeserializeStrategy(pingXmlDeSerializer));
    seda::Stage::Ptr pingXmlDeSerializerStage(new seda::Stage("tests.xbe.ping.stage.xml-deserialize", pingXmlDeSerializer));
    seda::StageRegistry::instance().insert(pingXmlDeSerializerStage);

    
    /*
     * Pong part
     *
     */

    /* PongClient stage */
    ::tests::xbe::PingPong::Ptr pongClient(new ::tests::xbe::PingPong("tests.xbe.pingpong.pong.stage.strategy",
                                                                      "tests.xbe.pong.stage.xml-serialize", // next stage
                                                                      "tests.xbe.pingpong.ping", // messages go to
                                                                      "tests.xbe.pingpong.pong", // messages come from
                                                                      numMsgs, // number of messages to send
                                                                      false // do not perform the initial send
                                                                      ));
    seda::Stage::Ptr pongClientStage(new seda::Stage("tests.xbe.pingpong.pong.stage", pongClient));
    seda::StageRegistry::instance().insert(pongClientStage);
    
    /* XML Serializer stage */
    seda::Strategy::Ptr pongXmlSerializer(new seda::ForwardStrategy("tests.xbe.pong.net"));
    pongXmlSerializer = seda::Strategy::Ptr(new ::xbe::XMLSerializeStrategy(pongXmlSerializer));
    seda::Stage::Ptr pongXmlSerializeStage(new seda::Stage("tests.xbe.pong.stage.xml-serialize", pongXmlSerializer));
    seda::StageRegistry::instance().insert(pongXmlSerializeStage);
    
    /* ChannelStub */
    seda::Strategy::Ptr pongNetStub(new seda::ForwardStrategy("tests.xbe.ping.stage.xml-deserialize"));
    seda::EventCountStrategy::Ptr ecsPongNetStub(new seda::EventCountStrategy(pongNetStub));
    pongNetStub = ecsPongNetStub;
    seda::Stage::Ptr pongNetStage(new seda::Stage("tests.xbe.pong.net", pongNetStub));
    seda::StageRegistry::instance().insert(pongNetStage);
    
    /* XML De-Serializer stage */
    seda::Strategy::Ptr pongXmlDeSerializer(new seda::ForwardStrategy("tests.xbe.pingpong.pong.stage"));
    pongXmlDeSerializer = seda::Strategy::Ptr(new ::xbe::XMLDeserializeStrategy(pongXmlDeSerializer));
    pongXmlDeSerializer = seda::Strategy::Ptr(new seda::LoggingStrategy(pongXmlDeSerializer));
    seda::Stage::Ptr pongXmlDeSerializerStage(new seda::Stage("tests.xbe.pong.stage.xml-deserialize", pongXmlDeSerializer));
    seda::StageRegistry::instance().insert(pongXmlDeSerializerStage);

    pingClientStage->start();
    pingXmlSerializeStage->start();
    pingNetStage->start();
    pingXmlDeSerializerStage->start();
    
    pongClientStage->start();
    pongXmlSerializeStage->start();
    pongNetStage->start();
    pongXmlDeSerializerStage->start();

    pongClient->doStart();
    pingClient->doStart();

    // wait until #msgs have been sent
    ecsPongNetStub->wait(numMsgs, 2000);
    ecsPingNetStub->wait(numMsgs, 2000);

    XBE_LOG_DEBUG("sent pings: " << ecsPingNetStub->count());
    XBE_LOG_DEBUG("sent pongs: " << ecsPongNetStub->count());

    pingClientStage->stop();
    pingXmlSerializeStage->stop();
    pingNetStage->stop();
    pingXmlDeSerializerStage->stop();
    
    pongClientStage->stop();
    pongXmlSerializeStage->stop();
    pongNetStage->stop();
    pongXmlDeSerializerStage->stop();

    pongClient->doStop();
    pingClient->doStop();
    
    CPPUNIT_ASSERT(ecsPingNetStub->count() == numMsgs);
    CPPUNIT_ASSERT(ecsPongNetStub->count() == numMsgs);
}


void
PingPongTest::testPingPongComplete() {
    /*
                  xml
FSM <- PingClient --> XMLSerializer --> ChannelAdapter <--> Channel <--> ChannelAdapter --> XMLDeserializer ---> PongClient --> FSM
       ^                                    |                               ^                                                    |
       |                                    |                               |                                                    |
       +------------ XMLDeserializer <------+                               +-------------- XMLSerializer <----------------------+
    */

    const std::size_t numMsgs(5);
    
    
    /*
     * Ping part
     *
     */

    /* PingClient stage */
    ::tests::xbe::PingPong::Ptr pingClient(new ::tests::xbe::PingPong("tests.xbe.pingpong.ping.stage.strategy",
                                                                      "tests.xbe.ping.stage.xml-serialize", // next stage
                                                                      "tests.xbe.pingpong.pong", // messages go to
                                                                      "tests.xbe.pingpong.ping", // messages come from
                                                                      numMsgs, // number of messages to send
                                                                      true // perform the initial send
                                                                      ));
    seda::Stage::Ptr pingClientStage(new seda::Stage("tests.xbe.pingpong.ping.stage", pingClient));
    seda::StageRegistry::instance().insert(pingClientStage);
    
    /* XML Serializer stage */
    seda::Strategy::Ptr pingXmlSerializer(new seda::ForwardStrategy("tests.xbe.ping.net"));
    pingXmlSerializer = seda::Strategy::Ptr(new seda::LoggingStrategy(pingXmlSerializer));
    pingXmlSerializer = seda::Strategy::Ptr(new ::xbe::XMLSerializeStrategy(pingXmlSerializer));
    seda::Stage::Ptr pingXmlSerializeStage(new seda::Stage("tests.xbe.ping.stage.xml-serialize", pingXmlSerializer));
    seda::StageRegistry::instance().insert(pingXmlSerializeStage);
    
    /* Channel stage */
    mqs::Channel::Ptr pingChannel(new mqs::Channel(mqs::BrokerURI(TEST_BROKER_URI),
                                                   mqs::Destination("tests.xbe.pingpong.ping")));
    seda::Strategy::Ptr pingNet(new ::xbe::ChannelAdapterStrategy("tests.xbe.ping.channeladapter",
                                                                  seda::Strategy::Ptr(new seda::ForwardStrategy("tests.xbe.ping.stage.xml-deserialize")),
                                                                  pingChannel));
    seda::EventCountStrategy::Ptr ecsPingNet(new seda::EventCountStrategy(pingNet));
    pingNet = ecsPingNet;
    seda::Stage::Ptr pingNetStage(new seda::Stage("tests.xbe.ping.net", pingNet));
    seda::StageRegistry::instance().insert(pingNetStage);
    
    /* XML De-Serializer stage */
    seda::Strategy::Ptr pingXmlDeSerializer(new seda::ForwardStrategy("tests.xbe.pingpong.ping.stage"));
    pingXmlDeSerializer = seda::Strategy::Ptr(new ::xbe::XMLDeserializeStrategy(pingXmlDeSerializer));
    seda::Stage::Ptr pingXmlDeSerializerStage(new seda::Stage("tests.xbe.ping.stage.xml-deserialize", pingXmlDeSerializer));
    seda::StageRegistry::instance().insert(pingXmlDeSerializerStage);

    
    /*
     * Pong part
     *
     */

    /* PongClient stage */
    ::tests::xbe::PingPong::Ptr pongClient(new ::tests::xbe::PingPong("tests.xbe.pingpong.pong.stage.strategy",
                                                                      "tests.xbe.pong.stage.xml-serialize", // next stage
                                                                      "tests.xbe.pingpong.ping", // messages go to
                                                                      "tests.xbe.pingpong.pong", // messages come from
                                                                      numMsgs, // number of messages to send
                                                                      false // do not perform the initial send
                                                                      ));
    seda::Stage::Ptr pongClientStage(new seda::Stage("tests.xbe.pingpong.pong.stage", pongClient));
    seda::StageRegistry::instance().insert(pongClientStage);
    
    /* XML Serializer stage */
    seda::Strategy::Ptr pongXmlSerializer(new seda::ForwardStrategy("tests.xbe.pong.net"));
    pongXmlSerializer = seda::Strategy::Ptr(new ::xbe::XMLSerializeStrategy(pongXmlSerializer));
    seda::Stage::Ptr pongXmlSerializeStage(new seda::Stage("tests.xbe.pong.stage.xml-serialize", pongXmlSerializer));
    seda::StageRegistry::instance().insert(pongXmlSerializeStage);
    
    /* Channel stage */
    mqs::Channel::Ptr pongChannel(new mqs::Channel(mqs::BrokerURI(TEST_BROKER_URI),
                                                   mqs::Destination("tests.xbe.pingpong.pong")));
    seda::Strategy::Ptr pongNet(new ::xbe::ChannelAdapterStrategy("tests.xbe.pong.channeladapter",
                                                                  seda::Strategy::Ptr(new seda::ForwardStrategy("tests.xbe.pong.stage.xml-deserialize")),
                                                                  pongChannel));
    seda::EventCountStrategy::Ptr ecsPongNet(new seda::EventCountStrategy(pongNet));
    pongNet = ecsPongNet;
    seda::Stage::Ptr pongNetStage(new seda::Stage("tests.xbe.pong.net", pongNet));
    seda::StageRegistry::instance().insert(pongNetStage);

    /* XML De-Serializer stage */
    seda::Strategy::Ptr pongXmlDeSerializer(new seda::ForwardStrategy("tests.xbe.pingpong.pong.stage"));
    pongXmlDeSerializer = seda::Strategy::Ptr(new ::xbe::XMLDeserializeStrategy(pongXmlDeSerializer));
    pongXmlDeSerializer = seda::Strategy::Ptr(new seda::LoggingStrategy(pongXmlDeSerializer));
    seda::Stage::Ptr pongXmlDeSerializerStage(new seda::Stage("tests.xbe.pong.stage.xml-deserialize", pongXmlDeSerializer));
    seda::StageRegistry::instance().insert(pongXmlDeSerializerStage);

    pingClientStage->start();
    pingXmlSerializeStage->start();
    pingNetStage->start();
    pingXmlDeSerializerStage->start();
    
    pongClientStage->start();
    pongXmlSerializeStage->start();
    pongNetStage->start();
    pongXmlDeSerializerStage->start();

    pongClient->doStart();
    pingClient->doStart();

    // wait until #msgs have been sent
    ecsPongNet->wait(numMsgs, 2000);
    ecsPingNet->wait(numMsgs, 2000);

    XBE_LOG_DEBUG("sent pings: " << ecsPingNet->count());
    XBE_LOG_DEBUG("sent pongs: " << ecsPongNet->count());

    pingClientStage->stop();
    pingXmlSerializeStage->stop();
    pingNetStage->stop();
    pingXmlDeSerializerStage->stop();
    
    pongClientStage->stop();
    pongXmlSerializeStage->stop();
    pongNetStage->stop();
    pongXmlDeSerializerStage->stop();

    pongClient->doStop();
    pingClient->doStop();
    
    CPPUNIT_ASSERT(ecsPingNet->count() == numMsgs);
    CPPUNIT_ASSERT(ecsPongNet->count() == numMsgs);
}

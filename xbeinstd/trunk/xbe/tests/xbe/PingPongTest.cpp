#include <string>
#include <unistd.h>

#include <xbe/common.hpp>
#include <xbe/XbeLibUtils.hpp>
#include <xbe/ChannelAdapterStrategy.hpp>
#include <xbe/XMLValidator.hpp>
#include <xbe/XMLSigner.hpp>
#include <xbe/XMLSerializeStrategy.hpp>
#include <xbe/XMLDeserializeStrategy.hpp>
#include <xbe/XMLDataBinder.hpp>
#include <xbe/XMLDataUnbinder.hpp>
#include <xbe/XbeXMLMessageHandling.hpp>
#include <xbe/event/XMLMessageEvent.hpp>
#include <xbe/event/XMLEvent.hpp>

#include <seda/Stage.hpp>
#include <seda/IEvent.hpp>
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
    // register the test xml-namespace with the namespace map
    XbeLibUtils::namespace_infomap()["xbetest"].name = "http://www.xenbee.net/schema/2008/02/xbetest";
    char cwd[PATH_MAX];
    getcwd(cwd, PATH_MAX);
    XBE_LOG_DEBUG("current working dir: " << cwd);
    XbeLibUtils::schema_properties().schema_location("http://www.xenbee.net/schema/2008/02/xbetest", std::string(cwd)+"/resources//xbe-test.xsd");
}

void
PingPongTest::tearDown() {
    seda::StageRegistry::instance().clear();
    XbeLibUtils::terminate();
}

void PingPongTest::testPingPong() {
    XBE_LOG_INFO("executing PingPongTest::testPingPong");

    /*
       xml                   ChannelStub
       FSM <- PingClient --> XMLSerializer ---> Forwarder --> XMLDeserializer ---> PongClient --> FSM
       ^                                                                             |
       |                                ChannelStub                                  |
       +------------ XMLDeserializer <-- Forwarder <--- XMLSerializer <--------------+
       */
    const std::size_t numMsgs(2);


    /*
     * Ping part
     *
     */

    /* PingClient stage */
    ::tests::xbe::PingPong::Ptr pingClient(new ::tests::xbe::PingPong("tests.xbe.pingpong.ping.stage.strategy",
                "tests.xbe.ping.stage.xml-unbind", // next stage
                "tests.xbe.pingpong.pong", // messages go to
                "tests.xbe.pingpong.ping", // messages come from
                numMsgs, // number of messages to send
                true // perform the initial send
                ));
    seda::Stage::Ptr pingClientStage(new seda::Stage("tests.xbe.pingpong.ping.stage", pingClient));
    seda::StageRegistry::instance().insert(pingClientStage);

    /* XML Unbind stage */
    seda::Strategy::Ptr pingXmlUnbinder(new seda::ForwardStrategy("tests.xbe.ping.stage.xml-serialize"));
    pingXmlUnbinder = seda::Strategy::Ptr(new seda::LoggingStrategy(pingXmlUnbinder));
    pingXmlUnbinder = seda::Strategy::Ptr(new ::xbe::XbeXMLDataUnbinder(pingXmlUnbinder));
    seda::Stage::Ptr pingXmlUnbindStage(new seda::Stage("tests.xbe.ping.stage.xml-unbind", pingXmlUnbinder));
    seda::StageRegistry::instance().insert(pingXmlUnbindStage);

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
    seda::Strategy::Ptr pingXmlDeSerializer(new seda::ForwardStrategy("tests.xbe.ping.stage.xml-bind"));
    pingXmlDeSerializer = seda::Strategy::Ptr(new ::xbe::XMLDeserializeStrategy(pingXmlDeSerializer));
    seda::Stage::Ptr pingXmlDeSerializerStage(new seda::Stage("tests.xbe.ping.stage.xml-deserialize", pingXmlDeSerializer));
    seda::StageRegistry::instance().insert(pingXmlDeSerializerStage);

    /* XML Data-Binder stage */
    seda::Strategy::Ptr pingXmlBinder(new seda::ForwardStrategy("tests.xbe.pingpong.ping.stage"));
    pingXmlBinder = seda::Strategy::Ptr(new ::xbe::XbeXMLDataBinder(pingXmlBinder));
    seda::Stage::Ptr pingXmlBindStage(new seda::Stage("tests.xbe.ping.stage.xml-bind", pingXmlBinder));
    seda::StageRegistry::instance().insert(pingXmlBindStage);


    /*
     * Pong part
     *
     */

    /* PongClient stage */
    ::tests::xbe::PingPong::Ptr pongClient(new ::tests::xbe::PingPong("tests.xbe.pingpong.pong.stage.strategy",
                "tests.xbe.pong.stage.xml-unbind", // next stage
                "tests.xbe.pingpong.ping", // messages go to
                "tests.xbe.pingpong.pong", // messages come from
                numMsgs, // number of messages to send
                false // do not perform the initial send
                ));
    seda::Stage::Ptr pongClientStage(new seda::Stage("tests.xbe.pingpong.pong.stage", pongClient));
    seda::StageRegistry::instance().insert(pongClientStage);

    /* XML Unbind stage */
    seda::Strategy::Ptr pongXmlUnbinder(new seda::ForwardStrategy("tests.xbe.pong.stage.xml-serialize"));
    pongXmlUnbinder = seda::Strategy::Ptr(new seda::LoggingStrategy(pongXmlUnbinder));
    pongXmlUnbinder = seda::Strategy::Ptr(new ::xbe::XbeXMLDataUnbinder(pongXmlUnbinder));
    seda::Stage::Ptr pongXmlUnbindStage(new seda::Stage("tests.xbe.pong.stage.xml-unbind", pongXmlUnbinder));
    seda::StageRegistry::instance().insert(pongXmlUnbindStage);

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
    seda::Strategy::Ptr pongXmlDeSerializer(new seda::ForwardStrategy("tests.xbe.pong.stage.xml-bind"));
    pongXmlDeSerializer = seda::Strategy::Ptr(new ::xbe::XMLDeserializeStrategy(pongXmlDeSerializer));
    pongXmlDeSerializer = seda::Strategy::Ptr(new seda::LoggingStrategy(pongXmlDeSerializer));
    seda::Stage::Ptr pongXmlDeSerializerStage(new seda::Stage("tests.xbe.pong.stage.xml-deserialize", pongXmlDeSerializer));
    seda::StageRegistry::instance().insert(pongXmlDeSerializerStage);

    /* XML Data-Binder stage */
    seda::Strategy::Ptr pongXmlBinder(new seda::ForwardStrategy("tests.xbe.pingpong.pong.stage"));
    pongXmlBinder = seda::Strategy::Ptr(new ::xbe::XbeXMLDataBinder(pongXmlBinder));
    seda::Stage::Ptr pongXmlBindStage(new seda::Stage("tests.xbe.pong.stage.xml-bind", pongXmlBinder));
    seda::StageRegistry::instance().insert(pongXmlBindStage);

    pingClientStage->start();
    pingXmlUnbindStage->start();
    pingXmlSerializeStage->start();
    pingNetStage->start();
    pingXmlDeSerializerStage->start();
    pingXmlBindStage->start();

    pongClientStage->start();
    pongXmlUnbindStage->start();
    pongXmlSerializeStage->start();
    pongNetStage->start();
    pongXmlDeSerializerStage->start();
    pongXmlBindStage->start();

    pongClient->doStart();
    pingClient->doStart();

    XBE_LOG_DEBUG("waiting for " << numMsgs << " sent messages." );
    // wait until #msgs have been sent
    ecsPongNetStub->wait(numMsgs, 1000);
    ecsPingNetStub->wait(numMsgs, 1000);

    XBE_LOG_DEBUG("sent pings: " << ecsPingNetStub->count());
    XBE_LOG_DEBUG("sent pongs: " << ecsPongNetStub->count());

    pingClientStage->stop();
    pingXmlUnbindStage->stop();
    pingXmlSerializeStage->stop();
    pingNetStage->stop();
    pingXmlDeSerializerStage->stop();
    pingXmlBindStage->stop();

    pongClientStage->stop();
    pongXmlUnbindStage->stop();
    pongXmlSerializeStage->stop();
    pongNetStage->stop();
    pongXmlDeSerializerStage->stop();
    pongXmlBindStage->stop();

    pongClient->doStop();
    pingClient->doStop();

    CPPUNIT_ASSERT(ecsPingNetStub->count() == numMsgs);
    CPPUNIT_ASSERT(ecsPongNetStub->count() == numMsgs);
}

void PingPongTest::testPingPongSigning() {
    XBE_LOG_INFO("executing PingPongTest::testPingPongSigning");

    /*
       xml                                 ChannelStub
       FSM <- PingClient --> XMLSigning --> XMLSerializer ---> Forwarder --> XMLDeserializer --> XMLValidator --> PongClient --> FSM
       ^                                                                                                       |
       |                                ChannelStub                                                            |
       `------------ XMLDeserializer <-- Forwarder <--- XMLSerializer <----------------------------------------´
       */

    const std::size_t numMsgs(2);


    /*
     * Ping part
     *
     */

    /* PingClient stage */
    ::tests::xbe::PingPong::Ptr pingClient(new ::tests::xbe::PingPong("tests.xbe.pingpong.ping.stage.strategy",
                "tests.xbe.ping.stage.xml-unbind", // next stage
                "tests.xbe.pingpong.pong", // messages go to
                "tests.xbe.pingpong.ping", // messages come from
                numMsgs, // number of messages to send
                true // perform the initial send
                ));
    seda::Stage::Ptr pingClientStage(new seda::Stage("tests.xbe.pingpong.ping.stage", pingClient));
    seda::StageRegistry::instance().insert(pingClientStage);

    /* XML Unbind stage */
    seda::Strategy::Ptr pingXmlUnbinder(new seda::ForwardStrategy("tests.xbe.ping.stage.xml-signer"));
    pingXmlUnbinder = seda::Strategy::Ptr(new seda::LoggingStrategy(pingXmlUnbinder));
    pingXmlUnbinder = seda::Strategy::Ptr(new ::xbe::XbeXMLDataUnbinder(pingXmlUnbinder));
    seda::Stage::Ptr pingXmlUnbindStage(new seda::Stage("tests.xbe.ping.stage.xml-unbind", pingXmlUnbinder));
    seda::StageRegistry::instance().insert(pingXmlUnbindStage);

    /* XML Signing stage */
    seda::Strategy::Ptr pingXmlSigner(new seda::ForwardStrategy("tests.xbe.ping.stage.xml-serialize"));
    pingXmlSigner = seda::Strategy::Ptr(new seda::LoggingStrategy(pingXmlSigner));
    pingXmlSigner = seda::Strategy::Ptr(new ::xbe::XMLSigner(pingXmlSigner));
    seda::Stage::Ptr pingXmlSignerStage(new seda::Stage("tests.xbe.ping.stage.xml-signer", pingXmlSigner));
    seda::StageRegistry::instance().insert(pingXmlSignerStage);

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
    seda::Strategy::Ptr pingXmlDeSerializer(new seda::ForwardStrategy("tests.xbe.ping.stage.xml-validator"));
    pingXmlDeSerializer = seda::Strategy::Ptr(new ::xbe::XMLDeserializeStrategy(pingXmlDeSerializer));
    seda::Stage::Ptr pingXmlDeSerializerStage(new seda::Stage("tests.xbe.ping.stage.xml-deserialize", pingXmlDeSerializer));
    seda::StageRegistry::instance().insert(pingXmlDeSerializerStage);

    /* XML Validating stage */
    seda::Strategy::Ptr pingXmlValidator(new seda::ForwardStrategy("tests.xbe.ping.stage.xml-bind"));
    pingXmlValidator = seda::Strategy::Ptr(new seda::LoggingStrategy(pingXmlValidator));
    pingXmlValidator = seda::Strategy::Ptr(new ::xbe::XMLValidator(pingXmlValidator));
    seda::Stage::Ptr pingXmlValidatorStage(new seda::Stage("tests.xbe.ping.stage.xml-validator", pingXmlValidator));
    seda::StageRegistry::instance().insert(pingXmlValidatorStage);

    /* XML Data-Binder stage */
    seda::Strategy::Ptr pingXmlBinder(new seda::ForwardStrategy("tests.xbe.pingpong.ping.stage"));
    pingXmlBinder = seda::Strategy::Ptr(new ::xbe::XbeXMLDataBinder(pingXmlBinder));
    seda::Stage::Ptr pingXmlBindStage(new seda::Stage("tests.xbe.ping.stage.xml-bind", pingXmlBinder));
    seda::StageRegistry::instance().insert(pingXmlBindStage);

    /*
     * Pong part
     *
     */

    /* PongClient stage */
    ::tests::xbe::PingPong::Ptr pongClient(new ::tests::xbe::PingPong("tests.xbe.pingpong.pong.stage.strategy",
                "tests.xbe.pong.stage.xml-unbind", // next stage
                "tests.xbe.pingpong.ping", // messages go to
                "tests.xbe.pingpong.pong", // messages come from
                numMsgs, // number of messages to send
                false // do not perform the initial send
                ));
    seda::Stage::Ptr pongClientStage(new seda::Stage("tests.xbe.pingpong.pong.stage", pongClient));
    seda::StageRegistry::instance().insert(pongClientStage);

    /* XML Unbind stage */
    seda::Strategy::Ptr pongXmlUnbinder(new seda::ForwardStrategy("tests.xbe.pong.stage.xml-signer"));
    pongXmlUnbinder = seda::Strategy::Ptr(new seda::LoggingStrategy(pongXmlUnbinder));
    pongXmlUnbinder = seda::Strategy::Ptr(new ::xbe::XbeXMLDataUnbinder(pongXmlUnbinder));
    seda::Stage::Ptr pongXmlUnbindStage(new seda::Stage("tests.xbe.pong.stage.xml-unbind", pongXmlUnbinder));
    seda::StageRegistry::instance().insert(pongXmlUnbindStage);

    /* XML Signing stage */
    seda::Strategy::Ptr pongXmlSigner(new seda::ForwardStrategy("tests.xbe.pong.stage.xml-serialize"));
    pongXmlSigner = seda::Strategy::Ptr(new seda::LoggingStrategy(pongXmlSigner));
    pongXmlSigner = seda::Strategy::Ptr(new ::xbe::XMLSigner(pongXmlSigner));
    seda::Stage::Ptr pongXmlSignerStage(new seda::Stage("tests.xbe.pong.stage.xml-signer", pongXmlSigner));
    seda::StageRegistry::instance().insert(pongXmlSignerStage);

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
    seda::Strategy::Ptr pongXmlDeSerializer(new seda::ForwardStrategy("tests.xbe.pong.stage.xml-validator"));
    pongXmlDeSerializer = seda::Strategy::Ptr(new ::xbe::XMLDeserializeStrategy(pongXmlDeSerializer));
    pongXmlDeSerializer = seda::Strategy::Ptr(new seda::LoggingStrategy(pongXmlDeSerializer));
    seda::Stage::Ptr pongXmlDeSerializerStage(new seda::Stage("tests.xbe.pong.stage.xml-deserialize", pongXmlDeSerializer));
    seda::StageRegistry::instance().insert(pongXmlDeSerializerStage);

    /* XML Validating stage */
    seda::Strategy::Ptr pongXmlValidator(new seda::ForwardStrategy("tests.xbe.pong.stage.xml-bind"));
    pongXmlValidator = seda::Strategy::Ptr(new seda::LoggingStrategy(pongXmlValidator));
    pongXmlValidator = seda::Strategy::Ptr(new ::xbe::XMLValidator(pongXmlValidator));
    seda::Stage::Ptr pongXmlValidatorStage(new seda::Stage("tests.xbe.pong.stage.xml-validator", pongXmlValidator));
    seda::StageRegistry::instance().insert(pongXmlValidatorStage);

    /* XML Data-Binder stage */
    seda::Strategy::Ptr pongXmlBinder(new seda::ForwardStrategy("tests.xbe.pingpong.pong.stage"));
    pongXmlBinder = seda::Strategy::Ptr(new ::xbe::XbeXMLDataBinder(pongXmlBinder));
    seda::Stage::Ptr pongXmlBindStage(new seda::Stage("tests.xbe.pong.stage.xml-bind", pongXmlBinder));
    seda::StageRegistry::instance().insert(pongXmlBindStage);

    pingClientStage->start();
    pingXmlUnbindStage->start();
    pingXmlSignerStage->start();
    pingXmlSerializeStage->start();
    pingNetStage->start();
    pingXmlDeSerializerStage->start();
    pingXmlValidatorStage->start();
    pingXmlBindStage->start();


    pongClientStage->start();
    pongXmlUnbindStage->start();
    pongXmlSignerStage->start();
    pongXmlSerializeStage->start();
    pongNetStage->start();
    pongXmlDeSerializerStage->start();
    pongXmlValidatorStage->start();
    pongXmlBindStage->start();

    pongClient->doStart();
    pingClient->doStart();

    // wait until #msgs have been sent
    ecsPongNetStub->wait(numMsgs, 1000);
    ecsPingNetStub->wait(numMsgs, 1000);

    XBE_LOG_DEBUG("sent pings: " << ecsPingNetStub->count());
    XBE_LOG_DEBUG("sent pongs: " << ecsPongNetStub->count());

    pingClientStage->stop();
    pingXmlUnbindStage->start();
    pingXmlSignerStage->stop();
    pingXmlSerializeStage->stop();
    pingNetStage->stop();
    pingXmlDeSerializerStage->stop();
    pingXmlValidatorStage->stop();
    pingXmlBindStage->stop();

    pongClientStage->stop();
    pongXmlUnbindStage->stop();
    pongXmlSignerStage->stop();
    pongXmlSerializeStage->stop();
    pongNetStage->stop();
    pongXmlDeSerializerStage->stop();
    pongXmlValidatorStage->stop();
    pongXmlBindStage->stop();
    pongClient->doStop();
    pingClient->doStop();

    CPPUNIT_ASSERT(ecsPingNetStub->count() == numMsgs);
    CPPUNIT_ASSERT(ecsPongNetStub->count() == numMsgs);
}

void
PingPongTest::testPingPongComplete() {
    XBE_LOG_INFO("executing PingPongTest::testPingPongComplete");

    /*
       xml
       FSM <- PingClient --> XMLSerializer --> ChannelAdapter <--> Channel <--> ChannelAdapter --> XMLDeserializer ---> PongClient --> FSM
       ^                                    |                               ^                                                    |
       |                                    |                               |                                                    |
       `------------ XMLDeserializer <------´                               `-------------- XMLSerializer <----------------------´
       */

    const std::size_t numMsgs(2);


    /*
     * Ping part
     *
     */

    /* PingClient stage */
    ::tests::xbe::PingPong::Ptr pingClient(new ::tests::xbe::PingPong("tests.xbe.pingpong.ping.stage.strategy",
                "tests.xbe.ping.stage.xml-unbind", // next stage
                "tests.xbe.pingpong.pong", // messages go to
                "tests.xbe.pingpong.ping", // messages come from
                numMsgs, // number of messages to send
                true // perform the initial send
                ));
    seda::Stage::Ptr pingClientStage(new seda::Stage("tests.xbe.pingpong.ping.stage", pingClient));
    seda::StageRegistry::instance().insert(pingClientStage);

    /* XML Unbind stage */
    seda::Strategy::Ptr pingXmlUnbinder(new seda::ForwardStrategy("tests.xbe.ping.stage.xml-serialize"));
    pingXmlUnbinder = seda::Strategy::Ptr(new seda::LoggingStrategy(pingXmlUnbinder));
    pingXmlUnbinder = seda::Strategy::Ptr(new ::xbe::XbeXMLDataUnbinder(pingXmlUnbinder));
    seda::Stage::Ptr pingXmlUnbindStage(new seda::Stage("tests.xbe.ping.stage.xml-unbind", pingXmlUnbinder));
    seda::StageRegistry::instance().insert(pingXmlUnbindStage);

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
    seda::Strategy::Ptr pingXmlDeSerializer(new seda::ForwardStrategy("tests.xbe.ping.stage.xml-bind"));
    pingXmlDeSerializer = seda::Strategy::Ptr(new ::xbe::XMLDeserializeStrategy(pingXmlDeSerializer));
    seda::Stage::Ptr pingXmlDeSerializerStage(new seda::Stage("tests.xbe.ping.stage.xml-deserialize", pingXmlDeSerializer));
    seda::StageRegistry::instance().insert(pingXmlDeSerializerStage);

    /* XML Data-Binder stage */
    seda::Strategy::Ptr pingXmlBinder(new seda::ForwardStrategy("tests.xbe.pingpong.ping.stage"));
    pingXmlBinder = seda::Strategy::Ptr(new ::xbe::XbeXMLDataBinder(pingXmlBinder));
    seda::Stage::Ptr pingXmlBindStage(new seda::Stage("tests.xbe.ping.stage.xml-bind", pingXmlBinder));
    seda::StageRegistry::instance().insert(pingXmlBindStage);

    /*
     * Pong part
     *
     */

    /* PongClient stage */
    ::tests::xbe::PingPong::Ptr pongClient(new ::tests::xbe::PingPong("tests.xbe.pingpong.pong.stage.strategy",
                "tests.xbe.pong.stage.xml-unbind", // next stage
                "tests.xbe.pingpong.ping", // messages go to
                "tests.xbe.pingpong.pong", // messages come from
                numMsgs, // number of messages to send
                false // do not perform the initial send
                ));
    seda::Stage::Ptr pongClientStage(new seda::Stage("tests.xbe.pingpong.pong.stage", pongClient));
    seda::StageRegistry::instance().insert(pongClientStage);

    /* XML Unbind stage */
    seda::Strategy::Ptr pongXmlUnbinder(new seda::ForwardStrategy("tests.xbe.pong.stage.xml-serialize"));
    pongXmlUnbinder = seda::Strategy::Ptr(new seda::LoggingStrategy(pongXmlUnbinder));
    pongXmlUnbinder = seda::Strategy::Ptr(new ::xbe::XbeXMLDataUnbinder(pongXmlUnbinder));
    seda::Stage::Ptr pongXmlUnbindStage(new seda::Stage("tests.xbe.pong.stage.xml-unbind", pongXmlUnbinder));
    seda::StageRegistry::instance().insert(pongXmlUnbindStage);

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
    seda::Strategy::Ptr pongXmlDeSerializer(new seda::ForwardStrategy("tests.xbe.pong.stage.xml-bind"));
    pongXmlDeSerializer = seda::Strategy::Ptr(new ::xbe::XMLDeserializeStrategy(pongXmlDeSerializer));
    pongXmlDeSerializer = seda::Strategy::Ptr(new seda::LoggingStrategy(pongXmlDeSerializer));
    seda::Stage::Ptr pongXmlDeSerializerStage(new seda::Stage("tests.xbe.pong.stage.xml-deserialize", pongXmlDeSerializer));
    seda::StageRegistry::instance().insert(pongXmlDeSerializerStage);

    /* XML Data-Binder stage */
    seda::Strategy::Ptr pongXmlBinder(new seda::ForwardStrategy("tests.xbe.pingpong.pong.stage"));
    pongXmlBinder = seda::Strategy::Ptr(new ::xbe::XbeXMLDataBinder(pongXmlBinder));
    seda::Stage::Ptr pongXmlBindStage(new seda::Stage("tests.xbe.pong.stage.xml-bind", pongXmlBinder));
    seda::StageRegistry::instance().insert(pongXmlBindStage);

    pingChannel->start();
    pingChannel->flushMessages();
    pongChannel->start();
    pongChannel->flushMessages();

    pingClientStage->start();
    pingXmlUnbindStage->start();
    pingXmlSerializeStage->start();
    pingNetStage->start();
    pingXmlDeSerializerStage->start();
    pingXmlBindStage->start();

    pongClientStage->start();
    pongXmlUnbindStage->start();
    pongXmlSerializeStage->start();
    pongNetStage->start();
    pongXmlDeSerializerStage->start();
    pongXmlBindStage->start();

    pongClient->doStart();
    pingClient->doStart();

    // wait until #msgs have been sent
    ecsPongNet->wait(numMsgs, 1000);
    ecsPingNet->wait(numMsgs, 1000);

    XBE_LOG_DEBUG("sent pings: " << ecsPingNet->count());
    XBE_LOG_DEBUG("sent pongs: " << ecsPongNet->count());

    pingClientStage->stop();
    pingXmlUnbindStage->stop();
    pingXmlSerializeStage->stop();
    pingNetStage->stop();
    pingXmlDeSerializerStage->stop();
    pingXmlBindStage->stop();

    pongClientStage->stop();
    pongXmlUnbindStage->stop();
    pongXmlSerializeStage->stop();
    pongNetStage->stop();
    pongXmlDeSerializerStage->stop();
    pongXmlBindStage->stop();

    pongClient->doStop();
    pingClient->doStop();

    pongChannel->stop();
    pingChannel->stop();

    CPPUNIT_ASSERT(ecsPingNet->count() == numMsgs);
    CPPUNIT_ASSERT(ecsPongNet->count() == numMsgs);
}

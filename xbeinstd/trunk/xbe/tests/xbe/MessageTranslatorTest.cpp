#include "testsconfig.hpp"
#include "MessageTranslatorTest.hpp"

#include <string>

#include <seda/Stage.hpp>
#include <seda/EventQueue.hpp>
#include <seda/IEvent.hpp>
#include <seda/StageRegistry.hpp>
#include <seda/ForwardStrategy.hpp>
#include <seda/EventCountStrategy.hpp>
#include <seda/DiscardStrategy.hpp>
#include <seda/LoggingStrategy.hpp>
#include <seda/AccumulateStrategy.hpp>

#include <xbe/XbeLibUtils.hpp>
#include <xbe/XMLParserPool.hpp>
#include <xbe/MessageTranslatorStrategy.hpp>
#include <xbe/event/ObjectEvent.hpp>
#include <xbe/event/ExecuteEvent.hpp>
#include <xbe/event/ExecuteAckEvent.hpp>
#include <xbe/event/StatusEvent.hpp>
#include <xbe/event/StatusReqEvent.hpp>
#include <xbe/event/FinishedEvent.hpp>
#include <xbe/event/TerminateAckEvent.hpp>
#include <xbe/event/LifeSignEvent.hpp>
#include <xbe/event/ShutdownEvent.hpp>
#include <xbe/event/ShutdownAckEvent.hpp>
#include <xbe/event/FailedEvent.hpp>

#include <xbe/xbe-msg.hpp>
#include <xbe/jsdl.hpp>
#include <xbe/jsdl-posix.hpp>

using namespace xbe::tests;

CPPUNIT_TEST_SUITE_REGISTRATION( MessageTranslatorTest );

MessageTranslatorTest::MessageTranslatorTest()
    : XBE_INIT_LOGGER("tests.xbe.message-translator")
{
    XbeLibUtils::initialise();
}

MessageTranslatorTest::~MessageTranslatorTest() {
    XbeLibUtils::terminate();
}

void
MessageTranslatorTest::setUp() {
    seda::StageRegistry::instance().clear();
}

void
MessageTranslatorTest::tearDown() {
}

void
MessageTranslatorTest::testXMLExecute() {
    XBE_LOG_DEBUG("***** Running testXMLExecute");

    try {
        XBE_LOG_DEBUG("parsing xml message");
    
        std::auto_ptr<xbemsg::message_t> msg;
        for (int i = 0; i < 5; i++) {
            std::ifstream ifs("resources/execute-msg1.xml");
            CPPUNIT_ASSERT_MESSAGE("could not open resources/execute-msg1.xml", ifs.good());
            msg = xbemsg::message(*XbeLibUtils::parse(ifs, "resources/execute-msg1.xml", true),
                                                      xml_schema::flags::dont_initialize | xml_schema::flags::keep_dom,
                                                      XbeLibUtils::schema_properties());
        }

        seda::Strategy::Ptr discard(new seda::DiscardStrategy());
        seda::AccumulateStrategy::Ptr acc(new seda::AccumulateStrategy(discard));
        seda::Strategy::Ptr translate(new xbe::MessageTranslatorStrategy(acc));
        translate = seda::Strategy::Ptr(new seda::LoggingStrategy(translate));
        seda::IEvent::Ptr obj(new xbe::event::ObjectEvent<xbemsg::message_t>("foo","bar",msg));

        XBE_LOG_DEBUG("translating the message to an event");
        translate->perform(obj);

        CPPUNIT_ASSERT(acc->begin() != acc->end());
        xbe::event::ExecuteEvent *execEvt(dynamic_cast<xbe::event::ExecuteEvent*>(acc->begin()->get()));
        CPPUNIT_ASSERT(execEvt != NULL);
        CPPUNIT_ASSERT_EQUAL(std::size_t(2), execEvt->taskData().params().size());
        CPPUNIT_ASSERT_EQUAL(std::string("/bin/sleep"), execEvt->taskData().path());
        CPPUNIT_ASSERT_EQUAL(std::string("10"), execEvt->taskData().params()[1]);
        CPPUNIT_ASSERT_EQUAL(std::string("/spool"), execEvt->taskData().wd().string());
        CPPUNIT_ASSERT(execEvt->taskData().env().size() > 0);
        CPPUNIT_ASSERT_EQUAL(std::string("/spool/foo"), execEvt->taskData().env()["FOO"]);
    } catch (const xml_schema::exception &e) {
        XBE_LOG_FATAL(e);
        CPPUNIT_ASSERT_MESSAGE(e.what(), false);
    }
}

void
MessageTranslatorTest::testXMLExecute2() {
    XBE_LOG_DEBUG("***** Running testXMLExecute2");

    try {
        XBE_LOG_DEBUG("parsing xml message");
        std::ifstream ifs("resources/execute-msg2.xml");
        CPPUNIT_ASSERT_MESSAGE("could not open resources/execute-msg2.xml", ifs.good());

        std::auto_ptr<xbemsg::message_t> msg = xbemsg::message(*XbeLibUtils::parse(ifs, "resources/execute-msg2.xml", true),
                                                               xml_schema::flags::dont_initialize | xml_schema::flags::keep_dom,
                                                               XbeLibUtils::schema_properties());

        seda::Strategy::Ptr discard(new seda::DiscardStrategy());
        seda::AccumulateStrategy::Ptr acc(new seda::AccumulateStrategy(discard));
        seda::Strategy::Ptr translate(new xbe::MessageTranslatorStrategy(acc));
        translate = seda::Strategy::Ptr(new seda::LoggingStrategy(translate));
        seda::IEvent::Ptr obj(new xbe::event::ObjectEvent<xbemsg::message_t>("foo","bar",msg));

        XBE_LOG_DEBUG("translating the message to an event");
        translate->perform(obj);

        CPPUNIT_ASSERT(acc->begin() != acc->end());
        xbe::event::ExecuteEvent *execEvt(dynamic_cast<xbe::event::ExecuteEvent*>(acc->begin()->get()));
        CPPUNIT_ASSERT(execEvt != NULL);
        CPPUNIT_ASSERT_EQUAL(std::size_t(2), execEvt->taskData().params().size());
        CPPUNIT_ASSERT_EQUAL(std::string("/bin/sleep"), execEvt->taskData().path());
        CPPUNIT_ASSERT_EQUAL(std::string("10"), execEvt->taskData().params()[1]);
        CPPUNIT_ASSERT_EQUAL(std::string("/spool"), execEvt->taskData().wd().string());
        CPPUNIT_ASSERT(execEvt->taskData().env().size() > 0);
        CPPUNIT_ASSERT_EQUAL(std::string("/spool/foo"), execEvt->taskData().env()["FOO"]);

        CPPUNIT_ASSERT(execEvt->statusTaskData().is_valid());
        CPPUNIT_ASSERT_EQUAL(std::size_t(2), execEvt->statusTaskData().params().size());
        CPPUNIT_ASSERT_EQUAL(std::string("/bin/ps"), execEvt->statusTaskData().path());
        CPPUNIT_ASSERT_EQUAL(std::string("aux"), execEvt->statusTaskData().params()[1]);
    } catch (const xml_schema::exception &e) {
        XBE_LOG_FATAL(e.what());
        CPPUNIT_ASSERT_MESSAGE(e.what(), false);
    }
}
void
MessageTranslatorTest::testXMLExecuteAck() {
    XBE_LOG_DEBUG("***** Running testXMLExecuteAck");

    xbemsg::header_t header("foo", "bar");
    header.conversation_id("conv-id:12345");
    xbemsg::body_t body;
    xbemsg::execute_ack_t exec_ack;
    body.execute_ack(exec_ack);

    std::auto_ptr<xbemsg::message_t> msg(new xbemsg::message_t(header, body));

    seda::Strategy::Ptr discard(new seda::DiscardStrategy());
    seda::AccumulateStrategy::Ptr acc(new seda::AccumulateStrategy(discard));
    seda::Strategy::Ptr translate(new xbe::MessageTranslatorStrategy(acc));
    translate = seda::Strategy::Ptr(new seda::LoggingStrategy(translate));

    seda::IEvent::Ptr obj(new xbe::event::ObjectEvent<xbemsg::message_t>("foo","bar",msg));
    translate->perform(obj);

    CPPUNIT_ASSERT(acc->begin() != acc->end());
    xbe::event::ExecuteAckEvent *evt(dynamic_cast<xbe::event::ExecuteAckEvent*>(acc->begin()->get()));
    CPPUNIT_ASSERT(evt != NULL);
}

void
MessageTranslatorTest::testExecuteAckEvent() {
    XBE_LOG_DEBUG("***** Running testExecuteAckEvent");

    seda::Strategy::Ptr discard(new seda::DiscardStrategy());
    seda::AccumulateStrategy::Ptr acc(new seda::AccumulateStrategy(discard));
    seda::Strategy::Ptr translate(new xbe::MessageTranslatorStrategy(acc));
    translate = seda::Strategy::Ptr(new seda::LoggingStrategy(translate));

    seda::IEvent::Ptr obj(new xbe::event::ExecuteAckEvent("foo","bar","conv-id:12345"));
    translate->perform(obj);

    CPPUNIT_ASSERT(acc->begin() != acc->end());
    xbe::event::ObjectEvent<xbemsg::message_t> *msgEvt(dynamic_cast<xbe::event::ObjectEvent<xbemsg::message_t>*>(acc->begin()->get()));
    std::auto_ptr<xbemsg::message_t> msg(msgEvt->object());
    XBE_LOG_DEBUG("conv-id: " << msg->header().conversation_id());
    CPPUNIT_ASSERT(msg->header().conversation_id() == "conv-id:12345");
    CPPUNIT_ASSERT(msg->body().execute_ack());
}

void
MessageTranslatorTest::testXMLStatusReq() {
    XBE_LOG_DEBUG("***** Running testXMLStatusReq");

    xbemsg::header_t header("foo", "bar");
    header.conversation_id("conv-id:12345");
    xbemsg::body_t body;
    xbemsg::status_req_t status_req;
    body.status_req(status_req);

    std::auto_ptr<xbemsg::message_t> msg(new xbemsg::message_t(header, body));

    seda::Strategy::Ptr discard(new seda::DiscardStrategy());
    seda::AccumulateStrategy::Ptr acc(new seda::AccumulateStrategy(discard));
    seda::Strategy::Ptr translate(new xbe::MessageTranslatorStrategy(acc));
    translate = seda::Strategy::Ptr(new seda::LoggingStrategy(translate));

    seda::IEvent::Ptr obj(new xbe::event::ObjectEvent<xbemsg::message_t>("foo","bar",msg));
    translate->perform(obj);

    CPPUNIT_ASSERT(acc->begin() != acc->end());
    xbe::event::StatusReqEvent *evt(dynamic_cast<xbe::event::StatusReqEvent*>(acc->begin()->get()));
    CPPUNIT_ASSERT(evt != NULL);
}

void
MessageTranslatorTest::testStatusReqEvent() {
    XBE_LOG_DEBUG("***** Running testStatusReqEvent");

    seda::Strategy::Ptr discard(new seda::DiscardStrategy());
    seda::AccumulateStrategy::Ptr acc(new seda::AccumulateStrategy(discard));
    seda::Strategy::Ptr translate(new xbe::MessageTranslatorStrategy(acc));
    translate = seda::Strategy::Ptr(new seda::LoggingStrategy(translate));

    seda::IEvent::Ptr obj(new xbe::event::StatusReqEvent("foo","bar","conv-id:12345"));
    translate->perform(obj);

    CPPUNIT_ASSERT(acc->begin() != acc->end());
    xbe::event::ObjectEvent<xbemsg::message_t> *msgEvt(dynamic_cast<xbe::event::ObjectEvent<xbemsg::message_t>*>(acc->begin()->get()));
    std::auto_ptr<xbemsg::message_t> msg(msgEvt->object());
    XBE_LOG_DEBUG("conv-id: " << msg->header().conversation_id());
    CPPUNIT_ASSERT(msg->header().conversation_id() == "conv-id:12345");
    CPPUNIT_ASSERT(msg->body().status_req());
}

void
MessageTranslatorTest::testXMLLifeSign() {
    XBE_LOG_DEBUG("***** Running testXMLLifeSign");

    xbemsg::header_t header("foo", "bar");
    header.conversation_id("conv-id:12345");
    xbemsg::body_t body;
    xbemsg::life_sign_t life_sign(time(0));
    body.life_sign(life_sign);

    std::auto_ptr<xbemsg::message_t> msg(new xbemsg::message_t(header, body));

    seda::Strategy::Ptr discard(new seda::DiscardStrategy());
    seda::AccumulateStrategy::Ptr acc(new seda::AccumulateStrategy(discard));
    seda::Strategy::Ptr translate(new xbe::MessageTranslatorStrategy(acc));
    translate = seda::Strategy::Ptr(new seda::LoggingStrategy(translate));

    seda::IEvent::Ptr obj(new xbe::event::ObjectEvent<xbemsg::message_t>("foo","bar",msg));
    translate->perform(obj);

    CPPUNIT_ASSERT(acc->begin() != acc->end());
    xbe::event::LifeSignEvent *evt(dynamic_cast<xbe::event::LifeSignEvent*>(acc->begin()->get()));
    CPPUNIT_ASSERT(evt != NULL);
}

void
MessageTranslatorTest::testLifeSignEvent() {
    XBE_LOG_DEBUG("***** Running testLifeSignEvent");

    seda::Strategy::Ptr discard(new seda::DiscardStrategy());
    seda::AccumulateStrategy::Ptr acc(new seda::AccumulateStrategy(discard));
    seda::Strategy::Ptr translate(new xbe::MessageTranslatorStrategy(acc));
    translate = seda::Strategy::Ptr(new seda::LoggingStrategy(translate));

    seda::IEvent::Ptr obj(new xbe::event::LifeSignEvent("foo","bar","conv-id:12345"));
    translate->perform(obj);

    CPPUNIT_ASSERT(acc->begin() != acc->end());
    xbe::event::ObjectEvent<xbemsg::message_t> *msgEvt(dynamic_cast<xbe::event::ObjectEvent<xbemsg::message_t>*>(acc->begin()->get()));
    std::auto_ptr<xbemsg::message_t> msg(msgEvt->object());
    XBE_LOG_DEBUG("conv-id: " << msg->header().conversation_id());
    CPPUNIT_ASSERT(msg->header().conversation_id() == "conv-id:12345");
    CPPUNIT_ASSERT(msg->body().life_sign());
}

void
MessageTranslatorTest::testXMLStatus() {
    XBE_LOG_DEBUG("***** Running testXMLStatus");

    xbemsg::header_t header("foo", "bar");
    header.conversation_id("conv-id:12345");
    xbemsg::body_t body;
    xbemsg::status_t status(time(0), -1);
    body.status(status);

    std::auto_ptr<xbemsg::message_t> msg(new xbemsg::message_t(header, body));

    seda::Strategy::Ptr discard(new seda::DiscardStrategy());
    seda::AccumulateStrategy::Ptr acc(new seda::AccumulateStrategy(discard));
    seda::Strategy::Ptr translate(new xbe::MessageTranslatorStrategy(acc));
    translate = seda::Strategy::Ptr(new seda::LoggingStrategy(translate));

    seda::IEvent::Ptr obj(new xbe::event::ObjectEvent<xbemsg::message_t>("foo","bar",msg));
    translate->perform(obj);

    CPPUNIT_ASSERT(acc->begin() != acc->end());
    xbe::event::StatusEvent *evt(dynamic_cast<xbe::event::StatusEvent*>(acc->begin()->get()));
    CPPUNIT_ASSERT(evt != NULL);
    CPPUNIT_ASSERT_EQUAL((unsigned int)status.timestamp(), evt->timestamp());
    CPPUNIT_ASSERT_EQUAL((int)status.exitcode(), evt->taskStatusCode());
}

void
MessageTranslatorTest::testStatusEvent() {
    XBE_LOG_DEBUG("***** Running testStatusEvent");

    seda::Strategy::Ptr discard(new seda::DiscardStrategy());
    seda::AccumulateStrategy::Ptr acc(new seda::AccumulateStrategy(discard));
    seda::Strategy::Ptr translate(new xbe::MessageTranslatorStrategy(acc));
    translate = seda::Strategy::Ptr(new seda::LoggingStrategy(translate));

    xbe::event::StatusEvent::Ptr obj(new xbe::event::StatusEvent("foo","bar","conv-id:12345"));
    obj->taskStatusCode(10);
    obj->taskStatusStdOut("Hello World!");
    obj->taskStatusStdErr("Hello World!");
    translate->perform(obj);

    CPPUNIT_ASSERT(acc->begin() != acc->end());
    xbe::event::ObjectEvent<xbemsg::message_t> *msgEvt(dynamic_cast<xbe::event::ObjectEvent<xbemsg::message_t>*>(acc->begin()->get()));
    std::auto_ptr<xbemsg::message_t> msg(msgEvt->object());
    XBE_LOG_DEBUG("conv-id: " << msg->header().conversation_id());
    CPPUNIT_ASSERT(msg->header().conversation_id() == "conv-id:12345");
    CPPUNIT_ASSERT(msg->body().status());
    CPPUNIT_ASSERT_EQUAL(10, (int)msg->body().status()->exitcode());

    std::string out(msg->body().status()->stdout()->data(), msg->body().status()->stdout()->size());
    std::string err(msg->body().status()->stderr()->data(), msg->body().status()->stderr()->size());

    CPPUNIT_ASSERT_EQUAL(obj->taskStatusStdOut(), out);
    CPPUNIT_ASSERT_EQUAL(obj->taskStatusStdErr(), err);
}

void
MessageTranslatorTest::testXMLFinished() {
    XBE_LOG_DEBUG("***** Running testXMLFinished");

    xbemsg::header_t header("foo", "bar");
    header.conversation_id("conv-id:12345");
    xbemsg::body_t body;
    xbemsg::finished_t finished(0);
    body.finished(finished);

    std::auto_ptr<xbemsg::message_t> msg(new xbemsg::message_t(header, body));

    seda::Strategy::Ptr discard(new seda::DiscardStrategy());
    seda::AccumulateStrategy::Ptr acc(new seda::AccumulateStrategy(discard));
    seda::Strategy::Ptr translate(new xbe::MessageTranslatorStrategy(acc));
    translate = seda::Strategy::Ptr(new seda::LoggingStrategy(translate));

    seda::IEvent::Ptr obj(new xbe::event::ObjectEvent<xbemsg::message_t>("foo","bar",msg));
    translate->perform(obj);

    CPPUNIT_ASSERT(acc->begin() != acc->end());
    xbe::event::FinishedEvent *evt(dynamic_cast<xbe::event::FinishedEvent*>(acc->begin()->get()));
    CPPUNIT_ASSERT(evt != NULL);
    CPPUNIT_ASSERT_EQUAL(0, evt->exitcode());
}

void
MessageTranslatorTest::testFinishedEvent() {
    XBE_LOG_DEBUG("***** Running testFinishedEvent");

    seda::Strategy::Ptr discard(new seda::DiscardStrategy());
    seda::AccumulateStrategy::Ptr acc(new seda::AccumulateStrategy(discard));
    seda::Strategy::Ptr translate(new xbe::MessageTranslatorStrategy(acc));
    translate = seda::Strategy::Ptr(new seda::LoggingStrategy(translate));

    seda::IEvent::Ptr obj(new xbe::event::FinishedEvent("foo","bar","conv-id:12345", 0));
    translate->perform(obj);

    CPPUNIT_ASSERT(acc->begin() != acc->end());
    xbe::event::ObjectEvent<xbemsg::message_t> *msgEvt(dynamic_cast<xbe::event::ObjectEvent<xbemsg::message_t>*>(acc->begin()->get()));
    std::auto_ptr<xbemsg::message_t> msg(msgEvt->object());
    XBE_LOG_DEBUG("conv-id: " << msg->header().conversation_id());
    CPPUNIT_ASSERT(msg->header().conversation_id() == "conv-id:12345");
    CPPUNIT_ASSERT(msg->body().finished());
    CPPUNIT_ASSERT_EQUAL((long long int)0, msg->body().finished()->exitcode());
}

void
MessageTranslatorTest::testXMLTerminateAck() {
    XBE_LOG_DEBUG("***** Running testXMLTerminateAck");

    xbemsg::header_t header("foo", "bar");
    header.conversation_id("conv-id:12345");
    xbemsg::body_t body;
    xbemsg::terminate_ack_t term_ack;
    body.terminate_ack(term_ack);

    std::auto_ptr<xbemsg::message_t> msg(new xbemsg::message_t(header, body));

    seda::Strategy::Ptr discard(new seda::DiscardStrategy());
    seda::AccumulateStrategy::Ptr acc(new seda::AccumulateStrategy(discard));
    seda::Strategy::Ptr translate(new xbe::MessageTranslatorStrategy(acc));
    translate = seda::Strategy::Ptr(new seda::LoggingStrategy(translate));

    seda::IEvent::Ptr obj(new xbe::event::ObjectEvent<xbemsg::message_t>("foo","bar",msg));
    translate->perform(obj);

    CPPUNIT_ASSERT(acc->begin() != acc->end());
    xbe::event::TerminateAckEvent *evt(dynamic_cast<xbe::event::TerminateAckEvent*>(acc->begin()->get()));
    CPPUNIT_ASSERT(evt != NULL);
}

void
MessageTranslatorTest::testTerminateAckEvent() {
    XBE_LOG_DEBUG("***** Running testTerminateAckEvent");

    seda::Strategy::Ptr discard(new seda::DiscardStrategy());
    seda::AccumulateStrategy::Ptr acc(new seda::AccumulateStrategy(discard));
    seda::Strategy::Ptr translate(new xbe::MessageTranslatorStrategy(acc));
    translate = seda::Strategy::Ptr(new seda::LoggingStrategy(translate));

    seda::IEvent::Ptr obj(new xbe::event::TerminateAckEvent("foo","bar","conv-id:12345"));
    translate->perform(obj);

    CPPUNIT_ASSERT(acc->begin() != acc->end());
    xbe::event::ObjectEvent<xbemsg::message_t> *msgEvt(dynamic_cast<xbe::event::ObjectEvent<xbemsg::message_t>*>(acc->begin()->get()));
    std::auto_ptr<xbemsg::message_t> msg(msgEvt->object());
    XBE_LOG_DEBUG("conv-id: " << msg->header().conversation_id());
    CPPUNIT_ASSERT(msg->header().conversation_id() == "conv-id:12345");
    CPPUNIT_ASSERT(msg->body().terminate_ack());
}

void
MessageTranslatorTest::testXMLShutdown() {
    XBE_LOG_DEBUG("***** Running testXMLShutdown");

    xbemsg::header_t header("foo", "bar");
    header.conversation_id("conv-id:12345");
    xbemsg::body_t body;
    xbemsg::shutdown_t elem;
    body.shutdown(elem);

    std::auto_ptr<xbemsg::message_t> msg(new xbemsg::message_t(header, body));

    seda::Strategy::Ptr discard(new seda::DiscardStrategy());
    seda::AccumulateStrategy::Ptr acc(new seda::AccumulateStrategy(discard));
    seda::Strategy::Ptr translate(new xbe::MessageTranslatorStrategy(acc));
    translate = seda::Strategy::Ptr(new seda::LoggingStrategy(translate));

    seda::IEvent::Ptr obj(new xbe::event::ObjectEvent<xbemsg::message_t>("foo","bar",msg));
    translate->perform(obj);

    CPPUNIT_ASSERT(acc->begin() != acc->end());
    xbe::event::ShutdownEvent *evt(dynamic_cast<xbe::event::ShutdownEvent*>(acc->begin()->get()));
    CPPUNIT_ASSERT(evt != NULL);
}

void
MessageTranslatorTest::testShutdownEvent() {
    XBE_LOG_DEBUG("***** Running testShutdownEvent");

    seda::Strategy::Ptr discard(new seda::DiscardStrategy());
    seda::AccumulateStrategy::Ptr acc(new seda::AccumulateStrategy(discard));
    seda::Strategy::Ptr translate(new xbe::MessageTranslatorStrategy(acc));
    translate = seda::Strategy::Ptr(new seda::LoggingStrategy(translate));

    seda::IEvent::Ptr obj(new xbe::event::ShutdownEvent("foo","bar","conv-id:12345"));
    translate->perform(obj);

    CPPUNIT_ASSERT(acc->begin() != acc->end());
    xbe::event::ObjectEvent<xbemsg::message_t> *msgEvt(dynamic_cast<xbe::event::ObjectEvent<xbemsg::message_t>*>(acc->begin()->get()));
    std::auto_ptr<xbemsg::message_t> msg(msgEvt->object());
    XBE_LOG_DEBUG("conv-id: " << msg->header().conversation_id());
    CPPUNIT_ASSERT(msg->header().conversation_id() == "conv-id:12345");
    CPPUNIT_ASSERT(msg->body().shutdown());
}

void
MessageTranslatorTest::testXMLShutdownAck() {
    XBE_LOG_DEBUG("***** Running testXMLShutdownAck");

    xbemsg::header_t header("foo", "bar");
    header.conversation_id("conv-id:12345");
    xbemsg::body_t body;
    xbemsg::shutdown_ack_t elem;
    body.shutdown_ack(elem);

    std::auto_ptr<xbemsg::message_t> msg(new xbemsg::message_t(header, body));

    seda::Strategy::Ptr discard(new seda::DiscardStrategy());
    seda::AccumulateStrategy::Ptr acc(new seda::AccumulateStrategy(discard));
    seda::Strategy::Ptr translate(new xbe::MessageTranslatorStrategy(acc));
    translate = seda::Strategy::Ptr(new seda::LoggingStrategy(translate));

    seda::IEvent::Ptr obj(new xbe::event::ObjectEvent<xbemsg::message_t>("foo","bar",msg));
    translate->perform(obj);

    CPPUNIT_ASSERT(acc->begin() != acc->end());
    xbe::event::ShutdownAckEvent *evt(dynamic_cast<xbe::event::ShutdownAckEvent*>(acc->begin()->get()));
    CPPUNIT_ASSERT(evt != NULL);
}

void
MessageTranslatorTest::testShutdownAckEvent() {
    XBE_LOG_DEBUG("***** Running testShutdownAckEvent");

    seda::Strategy::Ptr discard(new seda::DiscardStrategy());
    seda::AccumulateStrategy::Ptr acc(new seda::AccumulateStrategy(discard));
    seda::Strategy::Ptr translate(new xbe::MessageTranslatorStrategy(acc));
    translate = seda::Strategy::Ptr(new seda::LoggingStrategy(translate));

    seda::IEvent::Ptr obj(new xbe::event::ShutdownAckEvent("foo","bar","conv-id:12345"));
    translate->perform(obj);

    CPPUNIT_ASSERT(acc->begin() != acc->end());
    xbe::event::ObjectEvent<xbemsg::message_t> *msgEvt(dynamic_cast<xbe::event::ObjectEvent<xbemsg::message_t>*>(acc->begin()->get()));
    std::auto_ptr<xbemsg::message_t> msg(msgEvt->object());
    XBE_LOG_DEBUG("conv-id: " << msg->header().conversation_id());
    CPPUNIT_ASSERT(msg->header().conversation_id() == "conv-id:12345");
    CPPUNIT_ASSERT(msg->body().shutdown_ack());
}

void
MessageTranslatorTest::testXMLFailed() {
    XBE_LOG_DEBUG("***** Running testXMLFailed");

    xbemsg::header_t header("foo", "bar");
    header.conversation_id("conv-id:12345");
    xbemsg::body_t body;
    xbemsg::failed_t elem;
    body.failed(elem);

    std::auto_ptr<xbemsg::message_t> msg(new xbemsg::message_t(header, body));

    seda::Strategy::Ptr discard(new seda::DiscardStrategy());
    seda::AccumulateStrategy::Ptr acc(new seda::AccumulateStrategy(discard));
    seda::Strategy::Ptr translate(new xbe::MessageTranslatorStrategy(acc));
    translate = seda::Strategy::Ptr(new seda::LoggingStrategy(translate));

    seda::IEvent::Ptr obj(new xbe::event::ObjectEvent<xbemsg::message_t>("foo","bar",msg));
    translate->perform(obj);

    CPPUNIT_ASSERT(acc->begin() != acc->end());
    xbe::event::FailedEvent *evt(dynamic_cast<xbe::event::FailedEvent*>(acc->begin()->get()));
    CPPUNIT_ASSERT(evt != NULL);
}

void
MessageTranslatorTest::testFailedEvent() {
    XBE_LOG_DEBUG("***** Running testFailedEvent");

    seda::Strategy::Ptr discard(new seda::DiscardStrategy());
    seda::AccumulateStrategy::Ptr acc(new seda::AccumulateStrategy(discard));
    seda::Strategy::Ptr translate(new xbe::MessageTranslatorStrategy(acc));
    translate = seda::Strategy::Ptr(new seda::LoggingStrategy(translate));

    seda::IEvent::Ptr obj(new xbe::event::FailedEvent("foo","bar","conv-id:12345"));
    translate->perform(obj);

    CPPUNIT_ASSERT(acc->begin() != acc->end());
    xbe::event::ObjectEvent<xbemsg::message_t> *msgEvt(dynamic_cast<xbe::event::ObjectEvent<xbemsg::message_t>*>(acc->begin()->get()));
    std::auto_ptr<xbemsg::message_t> msg(msgEvt->object());
    XBE_LOG_DEBUG("conv-id: " << msg->header().conversation_id());
    CPPUNIT_ASSERT(msg->header().conversation_id() == "conv-id:12345");
    CPPUNIT_ASSERT(msg->body().failed());
}


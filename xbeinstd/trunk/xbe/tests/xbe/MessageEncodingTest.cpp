#include <string>
#include <iostream>
#include <unistd.h>

#include <xbe/common.hpp>
#include <xbe/TaskData.hpp>
#include <xbe/SerializeStrategy.hpp>
#include <xbe/DeserializeStrategy.hpp>

#include <xbe/event/ErrorMessageEvent.hpp>

#include <xbe/event/ShutdownEvent.hpp>
#include <xbe/event/ShutdownAckEvent.hpp>

#include <xbe/event/ExecuteEvent.hpp>
#include <xbe/event/ExecuteAckEvent.hpp>
#include <xbe/event/ExecuteNakEvent.hpp>

#include <xbe/event/TerminateEvent.hpp>
#include <xbe/event/TerminateAckEvent.hpp>

#include <xbe/event/FinishedEvent.hpp>
#include <xbe/event/FinishedAckEvent.hpp>

#include <xbe/event/FailedEvent.hpp>
#include <xbe/event/FailedAckEvent.hpp>

#include <xbe/event/StatusEvent.hpp>
#include <xbe/event/StatusReqEvent.hpp>

#include <xbe/event/LifeSignEvent.hpp>

#include <seda/Stage.hpp>
#include <seda/IEvent.hpp>
#include <seda/EventCountStrategy.hpp>
#include <seda/AccumulateStrategy.hpp>
#include <seda/StageFactory.hpp>
#include <seda/StageRegistry.hpp>
#include <seda/DiscardStrategy.hpp>
#include <seda/ForwardStrategy.hpp>
#include <seda/LoggingStrategy.hpp>
#include <seda/FilterStrategy.hpp>

#include "testsconfig.hpp"
#include "MessageEncodingTest.hpp"

using namespace xbe::tests;

CPPUNIT_TEST_SUITE_REGISTRATION( MessageEncodingTest );

MessageEncodingTest::MessageEncodingTest()
    : XBE_INIT_LOGGER("tests.xbe.msg-encoding")
{
}

MessageEncodingTest::~MessageEncodingTest() {
}

void
MessageEncodingTest::setUp() {
    seda::StageRegistry::instance().clear();
    seda::StageFactory::Ptr factory(new seda::StageFactory());

    seda::Strategy::Ptr encodeStrat(new xbe::SerializeStrategy("tests.xbe.serialize", "tests.xbe.deserialize"));
    _encode = factory->createStage("tests.xbe.serialize", encodeStrat);

    seda::Strategy::Ptr decodeStrat(new xbe::DeserializeStrategy("tests.xbe.deserialize", "tests.xbe.discard"));    
    _decode = factory->createStage("tests.xbe.deserialize", decodeStrat);

    seda::Strategy::Ptr discardStrat(new seda::DiscardStrategy());
    _ecs = seda::EventCountStrategy::Ptr(new seda::EventCountStrategy(discardStrat));
    _acc = seda::AccumulateStrategy::Ptr(new seda::AccumulateStrategy(_ecs));
    _discard = factory->createStage("tests.xbe.discard", _acc);

    seda::StageRegistry::instance().startAll();
}

void
MessageEncodingTest::tearDown() {
    seda::StageRegistry::instance().stopAll();

    _ecs.reset();
    _acc.reset();
    _discard.reset();
    _encode.reset();
    _decode.reset();

    seda::StageRegistry::instance().clear();
}

void MessageEncodingTest::testError () {
    xbe::event::ErrorMessageEvent::Ptr msg(new xbe::event::ErrorMessageEvent("conv-id:1234", "to", "from"));
    _encode->send(msg);
    _ecs->wait(1, 1000);
    
    const xbe::event::ErrorMessageEvent *evt = dynamic_cast<xbe::event::ErrorMessageEvent*>(_acc->begin()->get());
    CPPUNIT_ASSERT(evt != NULL);
}
void MessageEncodingTest::testExecute () {
    xbe::event::ExecuteEvent::Ptr msg(new xbe::event::ExecuteEvent("conv-id:1234", "to", "from"));
    _encode->send(msg);
    _ecs->wait(1, 1000);
    
    const xbe::event::ExecuteEvent *evt = dynamic_cast<xbe::event::ExecuteEvent*>(_acc->begin()->get());
    CPPUNIT_ASSERT(evt != NULL);

}
void MessageEncodingTest::testExecuteAck () {
    xbe::event::ExecuteAckEvent::Ptr msg(new xbe::event::ExecuteAckEvent("conv-id:1234", "to", "from"));
    _encode->send(msg);
    _ecs->wait(1, 1000);
    
    const xbe::event::ExecuteAckEvent *evt = dynamic_cast<xbe::event::ExecuteAckEvent*>(_acc->begin()->get());
    CPPUNIT_ASSERT(evt != NULL);
}
void MessageEncodingTest::testExecuteNak () {
    xbe::event::ExecuteNakEvent::Ptr msg(new xbe::event::ExecuteNakEvent("conv-id:1234", "to", "from"));
    _encode->send(msg);
    _ecs->wait(1, 1000);
    
    const xbe::event::ExecuteNakEvent *evt = dynamic_cast<xbe::event::ExecuteNakEvent*>(_acc->begin()->get());
    CPPUNIT_ASSERT(evt != NULL);
}
void MessageEncodingTest::testStatusReq () {
    xbe::event::StatusReqEvent::Ptr msg(new xbe::event::StatusReqEvent("conv-id:1234", "to", "from"));
    _encode->send(msg);
    _ecs->wait(1, 1000);
    
    const xbe::event::StatusReqEvent *evt = dynamic_cast<xbe::event::StatusReqEvent*>(_acc->begin()->get());
    CPPUNIT_ASSERT(evt != NULL);

}
void MessageEncodingTest::testStatus () {
    xbe::event::StatusEvent::Ptr msg(new xbe::event::StatusEvent("conv-id:1234", "to", "from"));
    _encode->send(msg);
    _ecs->wait(1, 1000);
    
    const xbe::event::StatusEvent *evt = dynamic_cast<xbe::event::StatusEvent*>(_acc->begin()->get());
    CPPUNIT_ASSERT(evt != NULL);

}
void MessageEncodingTest::testFinished () {
    xbe::event::FinishedEvent::Ptr msg(new xbe::event::FinishedEvent("conv-id:1234", "to", "from"));
    _encode->send(msg);
    _ecs->wait(1, 1000);
    
    const xbe::event::FinishedEvent *evt = dynamic_cast<xbe::event::FinishedEvent*>(_acc->begin()->get());
    CPPUNIT_ASSERT(evt != NULL);

}
void MessageEncodingTest::testFinishedAck () {
    xbe::event::FinishedAckEvent::Ptr msg(new xbe::event::FinishedAckEvent("conv-id:1234", "to", "from"));
    _encode->send(msg);
    _ecs->wait(1, 1000);
    
    const xbe::event::FinishedAckEvent *evt = dynamic_cast<xbe::event::FinishedAckEvent*>(_acc->begin()->get());
    CPPUNIT_ASSERT(evt != NULL);

}
void MessageEncodingTest::testFailed () {
    xbe::event::FailedEvent::Ptr msg(new xbe::event::FailedEvent("conv-id:1234", "to", "from"));
    _encode->send(msg);
    _ecs->wait(1, 1000);
    
    const xbe::event::FailedEvent *evt = dynamic_cast<xbe::event::FailedEvent*>(_acc->begin()->get());
    CPPUNIT_ASSERT(evt != NULL);

}
void MessageEncodingTest::testFailedAck () {
    xbe::event::FailedAckEvent::Ptr msg(new xbe::event::FailedAckEvent("conv-id:1234", "to", "from"));
    _encode->send(msg);
    _ecs->wait(1, 1000);
    
    const xbe::event::FailedAckEvent *evt = dynamic_cast<xbe::event::FailedAckEvent*>(_acc->begin()->get());
    CPPUNIT_ASSERT(evt != NULL);

}
void MessageEncodingTest::testShutdown () {
    xbe::event::ShutdownEvent::Ptr msg(new xbe::event::ShutdownEvent("conv-id:1234", "to", "from"));
    _encode->send(msg);
    _ecs->wait(1, 1000);
    
    const xbe::event::ShutdownEvent *evt = dynamic_cast<xbe::event::ShutdownEvent*>(_acc->begin()->get());
    CPPUNIT_ASSERT(evt != NULL);

}
void MessageEncodingTest::testShutdownAck () {
    xbe::event::ShutdownAckEvent::Ptr msg(new xbe::event::ShutdownAckEvent("conv-id:1234", "to", "from"));
    _encode->send(msg);
    _ecs->wait(1, 1000);
    
    const xbe::event::ShutdownAckEvent *evt = dynamic_cast<xbe::event::ShutdownAckEvent*>(_acc->begin()->get());
    CPPUNIT_ASSERT(evt != NULL);

}
void MessageEncodingTest::testTerminate () {
    xbe::event::TerminateEvent::Ptr msg(new xbe::event::TerminateEvent("conv-id:1234", "to", "from"));
    _encode->send(msg);
    _ecs->wait(1, 1000);
    
    const xbe::event::TerminateEvent *evt = dynamic_cast<xbe::event::TerminateEvent*>(_acc->begin()->get());
    CPPUNIT_ASSERT(evt != NULL);

}
void MessageEncodingTest::testTerminateAck () {
    xbe::event::TerminateAckEvent::Ptr msg(new xbe::event::TerminateAckEvent("conv-id:1234", "to", "from"));
    _encode->send(msg);
    _ecs->wait(1, 1000);
    
    const xbe::event::TerminateAckEvent *evt = dynamic_cast<xbe::event::TerminateAckEvent*>(_acc->begin()->get());
    CPPUNIT_ASSERT(evt != NULL);

}
void MessageEncodingTest::testLifeSign () {
    xbe::event::LifeSignEvent::Ptr msg(new xbe::event::LifeSignEvent("conv-id:1234", "to", "from"));
    _encode->send(msg);
    _ecs->wait(1, 1000);
    
    const xbe::event::LifeSignEvent *evt = dynamic_cast<xbe::event::LifeSignEvent*>(_acc->begin()->get());
    CPPUNIT_ASSERT(evt != NULL);

}

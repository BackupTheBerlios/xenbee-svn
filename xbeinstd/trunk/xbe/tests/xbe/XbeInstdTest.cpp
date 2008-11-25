#include <string>
#include <unistd.h>

#include <xbe/common.hpp>
#include <xbe/XbeInstd.hpp>
#include <xbe/event/ShutdownAckEvent.hpp>
#include <xbe/event/TerminateAckEvent.hpp>
#include <xbe/event/StatusEvent.hpp>

#include <seda/Stage.hpp>
#include <seda/IEvent.hpp>
#include <seda/EventCountStrategy.hpp>
#include <seda/AccumulateStrategy.hpp>
#include <seda/StageRegistry.hpp>
#include <seda/DiscardStrategy.hpp>
#include <seda/ForwardStrategy.hpp>
#include <seda/LoggingStrategy.hpp>

#include "testsconfig.hpp"
#include "XbeInstdTest.hpp"

using namespace xbe::tests;

CPPUNIT_TEST_SUITE_REGISTRATION( XbeInstdTest );

XbeInstdTest::XbeInstdTest()
    : XBE_INIT_LOGGER("tests.xbe.xbeinstd")
{}

void
XbeInstdTest::setUp() {
    xbe::XbeInstd::Ptr xbeinstd(new XbeInstd("xbeinstd", "discard", "to.foo", "from.bar"));
    _xbeInstdStage = seda::Stage::Ptr(new seda::Stage("xbeinstd", xbeinstd));
    seda::StageRegistry::instance().insert(_xbeInstdStage);

    seda::Strategy::Ptr discard(new seda::DiscardStrategy());
    _ecs = seda::EventCountStrategy::Ptr(new seda::EventCountStrategy(discard));
    _acc = seda::AccumulateStrategy::Ptr(new seda::AccumulateStrategy(_ecs));
    _discardStage = seda::Stage::Ptr(new seda::Stage("discard", _acc));
    seda::StageRegistry::instance().insert(_discardStage);
}

void
XbeInstdTest::tearDown() {
    seda::StageRegistry::instance().clear();
}

void XbeInstdTest::testLifeSign() {
    XBE_LOG_INFO("executing XbeInstdTest::testLifeSign");

    _discardStage->start();
    _xbeInstdStage->start();

    _ecs->wait(1, 4000);

    _xbeInstdStage->stop();
    _discardStage->stop();

    CPPUNIT_ASSERT(_ecs->count() > 0);
    // get the first IEvent out of the accu
    const seda::IEvent::Ptr e(*_acc->begin());
    CPPUNIT_ASSERT(dynamic_cast<xbe::event::LifeSignEvent*>(e.get()) != NULL);
}

void XbeInstdTest::testShutdown1() {
    XBE_LOG_INFO("executing XbeInstdTest::testShutdown1");

    _discardStage->start();
    _xbeInstdStage->start();

    seda::IEvent::Ptr shutdownEvent(new xbe::event::ShutdownEvent("from.bar", "to.bar", "1"));

    _xbeInstdStage->send(shutdownEvent);

    _ecs->wait(1, 4000);

    _xbeInstdStage->stop();
    _discardStage->stop();

    CPPUNIT_ASSERT(_ecs->count() > 0);

    bool gotAck(false);
    for (seda::AccumulateStrategy::const_iterator it = _acc->begin(); it != _acc->end(); it++) {
        if (dynamic_cast<xbe::event::ShutdownAckEvent*>((*it).get()) != NULL)
            gotAck=true;
    }
    CPPUNIT_ASSERT_EQUAL(true, gotAck);
}

void XbeInstdTest::testShutdown2() {
    XBE_LOG_INFO("executing XbeInstdTest::testShutdown2");

    _discardStage->start();

    /* send shutdown before start */
    seda::IEvent::Ptr shutdownEvent(new xbe::event::ShutdownEvent("from.bar", "to.bar", "1"));
    _xbeInstdStage->send(shutdownEvent);

    _xbeInstdStage->start();

    _ecs->wait(1, 4000);

    _xbeInstdStage->stop();
    _discardStage->stop();

    CPPUNIT_ASSERT(_ecs->count() > 0);

    bool gotAck(false);
    for (seda::AccumulateStrategy::const_iterator it = _acc->begin(); it != _acc->end(); it++) {
        if (dynamic_cast<xbe::event::ShutdownAckEvent*>((*it).get()) != NULL)
            gotAck=true;
    }
    CPPUNIT_ASSERT_EQUAL(true, gotAck);
}

void XbeInstdTest::testStatus1() {
    XBE_LOG_INFO("executing XbeInstdTest::testStatus1");

    _discardStage->start();
    _xbeInstdStage->start();

    seda::IEvent::Ptr statusReqEvent(new xbe::event::StatusReqEvent("from.bar", "to.bar", "1"));

    _xbeInstdStage->send(statusReqEvent);
    _ecs->wait(1, 4000);

    _xbeInstdStage->send(statusReqEvent);
    _ecs->wait(2, 4000);

    _xbeInstdStage->send(statusReqEvent);
    _ecs->wait(3, 4000);

    _xbeInstdStage->send(statusReqEvent);
    _ecs->wait(4, 4000);

    _xbeInstdStage->stop();
    _discardStage->stop();

    CPPUNIT_ASSERT(_ecs->count() > 0);

    int statusCount(0);
    for (seda::AccumulateStrategy::const_iterator it = _acc->begin(); it != _acc->end(); it++) {
        if (dynamic_cast<xbe::event::StatusEvent*>((*it).get()) != NULL)
            statusCount++;
    }
    CPPUNIT_ASSERT_EQUAL(4, statusCount);
}

void XbeInstdTest::testTerminate1() {
    XBE_LOG_INFO("executing XbeInstdTest::testTerminate1");

    _discardStage->start();
    _xbeInstdStage->start();

    seda::IEvent::Ptr terminateEvent(new xbe::event::TerminateEvent("from.bar", "to.bar", "1"));
    _xbeInstdStage->send(terminateEvent);

    _ecs->wait(1, 4000);

    _xbeInstdStage->stop();
    _discardStage->stop();

    CPPUNIT_ASSERT(_ecs->count() > 0);

    bool gotAck(false);
    for (seda::AccumulateStrategy::const_iterator it = _acc->begin(); it != _acc->end(); it++) {
        if (dynamic_cast<xbe::event::TerminateAckEvent*>((*it).get()) != NULL)
            gotAck=true;
    }
    CPPUNIT_ASSERT_EQUAL(true, gotAck);
}

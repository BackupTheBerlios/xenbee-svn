#include <string>
#include <iostream>
#include <unistd.h>

#include <xbe/common.hpp>
#include <xbe/XbeLibUtils.hpp>
#include <xbe/XbeInstd.hpp>
#include <xbe/TaskData.hpp>
#include <xbe/event/ShutdownAckEvent.hpp>
#include <xbe/event/ExecuteAckEvent.hpp>
#include <xbe/event/TerminateAckEvent.hpp>
#include <xbe/event/StatusEvent.hpp>

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
#include "XbeInstdTest.hpp"

using namespace xbe::tests;

CPPUNIT_TEST_SUITE_REGISTRATION( XbeInstdTest );

XbeInstdTest::XbeInstdTest()
    : XBE_INIT_LOGGER("tests.xbe.xbeinstd")
{}

void
XbeInstdTest::setUp() {
    XbeLibUtils::initialise();
    seda::StageFactory::Ptr factory(new seda::StageFactory());

    xbe::XbeInstd::Ptr xbeinstd(new XbeInstd("xbeinstd", seda::Strategy::Ptr(new seda::ForwardStrategy("discard")), "to.foo", "from.bar"));
    _xbeInstdStage = factory->createStage("xbeinstd", xbeinstd);

    seda::Strategy::Ptr discard(new seda::DiscardStrategy());
    _ecs = seda::EventCountStrategy::Ptr(new seda::EventCountStrategy(discard));
    _acc = seda::AccumulateStrategy::Ptr(new seda::AccumulateStrategy(_ecs));
    _discardStage = factory->createStage("discard", _acc);
}

void
XbeInstdTest::tearDown() {
    _xbeInstdStage.reset();
    _ecs.reset();
    _acc.reset();
    _discardStage.reset();

    seda::StageRegistry::instance().clear();

    // remove created files
    unlink("resources/testData.1.out");
    XbeLibUtils::terminate();
}

void XbeInstdTest::testLifeSign() {
    XBE_LOG_INFO("executing XbeInstdTest::testLifeSign");

    _xbeInstdStage->start();
    _discardStage->start();

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

    CPPUNIT_ASSERT(_ecs->count() > 3);

    int statusCount(0);
    for (seda::AccumulateStrategy::const_iterator it = _acc->begin(); it != _acc->end(); it++) {
        xbe::event::StatusEvent* stEvt = dynamic_cast<xbe::event::StatusEvent*>((*it).get());
        if ( stEvt != NULL) {
            statusCount++;
            CPPUNIT_ASSERT_EQUAL(std::string("Idle"), stEvt->state());
        }
    }
    CPPUNIT_ASSERT_EQUAL(4, statusCount);
}

void XbeInstdTest::testStatus2() {
    XBE_LOG_INFO("executing XbeInstdTest::testStatus2");

    _discardStage->start();
    _xbeInstdStage->start();

    _ecs->wait(1, 4000); // wait for life signal
    seda::IEvent::Ptr statusReqEvent(new xbe::event::StatusReqEvent("from.bar", "to.bar", "1"));
    _xbeInstdStage->send(statusReqEvent);

    TaskData td("/bin/sleep");
    td.params().push_back("10");

    std::tr1::shared_ptr<xbe::event::ExecuteEvent> executeEvent(new xbe::event::ExecuteEvent("from.bar", "to.bar", "1"));
    executeEvent->taskData(td);
    _xbeInstdStage->send(executeEvent);

    _xbeInstdStage->send(statusReqEvent);

    seda::IEvent::Ptr shutdownEvent(new xbe::event::ShutdownEvent("from.bar", "to.bar", "1"));
    _xbeInstdStage->send(shutdownEvent);

    _xbeInstdStage->waitUntilEmpty();
    _discardStage->waitUntilEmpty();

    _xbeInstdStage->stop();
    _discardStage->stop();

    CPPUNIT_ASSERT(_ecs->count() > 2);

    // event queue should contain: Status(Idle), ExecuteAck, Status(Busy), ShutdownAck
    // interleaved with LifeSigns
    {
        int lifeSignSeen(0);
        int statusIdleSeen(0);
        int statusBusySeen(0);
        int executeAckSeen(0);
        int shutdownAckSeen(0);

        for (seda::AccumulateStrategy::const_iterator it = _acc->begin(); it != _acc->end(); it++) {
            if (xbe::event::StatusEvent *evt = dynamic_cast<xbe::event::StatusEvent*>((*it).get())) {
                if (evt->state() == "Idle") statusIdleSeen++;
                if (evt->state() == "Busy") statusBusySeen++;
            } else if (xbe::event::LifeSignEvent *evt = dynamic_cast<xbe::event::LifeSignEvent*>((*it).get())) {
                lifeSignSeen++;
            } else if (xbe::event::ExecuteAckEvent *evt = dynamic_cast<xbe::event::ExecuteAckEvent*>((*it).get())) {
                executeAckSeen++;
            } else if (xbe::event::ShutdownAckEvent *evt = dynamic_cast<xbe::event::ShutdownAckEvent*>((*it).get())) {
                shutdownAckSeen++;
            }
        }
        CPPUNIT_ASSERT_EQUAL(1, statusIdleSeen);
        CPPUNIT_ASSERT_EQUAL(1, executeAckSeen);
        CPPUNIT_ASSERT_EQUAL(1, statusBusySeen);
        CPPUNIT_ASSERT_EQUAL(1, shutdownAckSeen);
        CPPUNIT_ASSERT(lifeSignSeen > 0);
    }
}
void XbeInstdTest::testTerminate1() {
    XBE_LOG_INFO("executing XbeInstdTest::testTerminate1");

    _discardStage->start();
    _xbeInstdStage->start();

    seda::IEvent::Ptr terminateEvent(new xbe::event::TerminateEvent("from.bar", "to.bar", "1"));
    _xbeInstdStage->send(terminateEvent);

    _ecs->wait(1, 4000);

    _xbeInstdStage->waitUntilEmpty();
    _discardStage->waitUntilEmpty();

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
void XbeInstdTest::testTerminate2() {
    XBE_LOG_INFO("executing XbeInstdTest::testTerminate2");

    _discardStage->start();
    _xbeInstdStage->start();

    TaskData td("/bin/sleep");
    td.params().push_back("3");

    std::tr1::shared_ptr<xbe::event::ExecuteEvent> executeEvent(new xbe::event::ExecuteEvent("from.bar", "to.bar", "1"));
    executeEvent->taskData(td);
    _xbeInstdStage->send(executeEvent);

    seda::IEvent::Ptr terminateEvent(new xbe::event::TerminateEvent("from.bar", "to.bar", "1"));
    _xbeInstdStage->send(terminateEvent);

    // just wait a bit
    _ecs->wait(5, 3000);

    seda::IEvent::Ptr shutdownEvent(new xbe::event::ShutdownEvent("from.bar", "to.bar", "1"));
    _xbeInstdStage->send(shutdownEvent);

    _xbeInstdStage->waitUntilEmpty();
    _discardStage->waitUntilEmpty();

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
void XbeInstdTest::testExecute1() {
    XBE_LOG_INFO("executing XbeInstdTest::testExecute1");

    _discardStage->start();
    _xbeInstdStage->start();

    TaskData td("/bin/sleep");
    td.params().push_back("3");

    std::tr1::shared_ptr<xbe::event::ExecuteEvent> executeEvent(new xbe::event::ExecuteEvent("from.bar", "to.bar", "1"));
    executeEvent->taskData(td);
    _xbeInstdStage->send(executeEvent);

    // just wait a bit
    _ecs->wait(10, 7000);

    seda::IEvent::Ptr shutdownEvent(new xbe::event::ShutdownEvent("from.bar", "to.bar", "1"));
    _xbeInstdStage->send(shutdownEvent);

    _xbeInstdStage->waitUntilEmpty();
    _discardStage->waitUntilEmpty();

    _xbeInstdStage->stop();
    _discardStage->stop();

    CPPUNIT_ASSERT(_ecs->count() > 0);

    bool gotAck(false);
    for (seda::AccumulateStrategy::const_iterator it = _acc->begin(); it != _acc->end(); it++) {
        if (dynamic_cast<xbe::event::FinishedEvent*>((*it).get()) != NULL)
            gotAck=true;
    }
    CPPUNIT_ASSERT_EQUAL(true, gotAck);
}
void XbeInstdTest::testExecute2() {
    XBE_LOG_INFO("executing XbeInstdTest::testExecute2");

    _discardStage->start();
    _xbeInstdStage->start();

    // wait for the first lifesign signal
    _ecs->wait(1, 3500);
    CPPUNIT_ASSERT_MESSAGE("first message was no LifeSign", dynamic_cast<xbe::event::LifeSignEvent*>(_acc->begin()->get()) != NULL);

    TaskData td("/bin/cat");
    td.stdIn("resources/testData.1");
    td.stdOut("resources/testData.1.out");

    std::tr1::shared_ptr<xbe::event::ExecuteEvent> executeEvent(new xbe::event::ExecuteEvent("from.bar", "to.bar", "1"));
    executeEvent->taskData(td);
    _xbeInstdStage->send(executeEvent);

    // just wait a bit
    _ecs->wait(10, 7000);

    seda::IEvent::Ptr shutdownEvent(new xbe::event::ShutdownEvent("from.bar", "to.bar", "1"));
    _xbeInstdStage->send(shutdownEvent);

    _xbeInstdStage->waitUntilEmpty();
    _discardStage->waitUntilEmpty();

    _xbeInstdStage->stop();
    _discardStage->stop();

    CPPUNIT_ASSERT(_ecs->count() > 0);

    bool gotAck(false);
    for (seda::AccumulateStrategy::const_iterator it = _acc->begin(); it != _acc->end(); it++) {
        if (dynamic_cast<xbe::event::FinishedEvent*>((*it).get()) != NULL)
            gotAck=true;
    }
    CPPUNIT_ASSERT_EQUAL(true, gotAck);

    // TODO: check if testData.1.out has been created and has the same content
    std::ifstream ifs("resources/testData.1.out");
    CPPUNIT_ASSERT_MESSAGE("Could not open resources/testData.1.out", ifs.good());
    std::string text;
    std::getline(ifs, text);
    CPPUNIT_ASSERT_EQUAL(std::string("Hello World"), text);
}


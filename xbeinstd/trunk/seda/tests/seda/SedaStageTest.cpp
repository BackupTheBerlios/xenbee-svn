#include "SedaStageTest.hpp"

#include <string>
#include <iostream>

#include <seda/Stage.hpp>
#include <seda/EventQueue.hpp>
#include <seda/IEvent.hpp>
#include <seda/StageRegistry.hpp>
#include <seda/EventCountStrategy.hpp>
#include <seda/CompositeStrategy.hpp>
#include <seda/AccumulateStrategy.hpp>
#include <seda/DiscardStrategy.hpp>
#include <seda/CoutStrategy.hpp>
#include <seda/ForwardStrategy.hpp>
#include <seda/LoggingStrategy.hpp>
#include <seda/StringEvent.hpp>

using namespace seda::tests;

CPPUNIT_TEST_SUITE_REGISTRATION( SedaStageTest );


void
SedaStageTest::setUp() {}

void
SedaStageTest::tearDown() {
    StageRegistry::instance().clear(); // remove all registered stages
}

void
SedaStageTest::testSendFoo() {
  seda::Strategy::Ptr discard(new seda::DiscardStrategy());
  seda::EventCountStrategy::Ptr ecs(new seda::EventCountStrategy(discard));
  discard = seda::Strategy::Ptr(ecs);
  seda::Stage::Ptr stage(new seda::Stage("discard", discard, 2));

  stage->start();

  const std::size_t numMsgs(10);
  for (std::size_t i=0; i < numMsgs; ++i) {
    stage->send(seda::IEvent::Ptr(new seda::StringEvent("foo")));
  }

  stage->waitUntilEmpty();
  ecs->wait(numMsgs, 1000);
  
  CPPUNIT_ASSERT(stage->queue()->empty());
  CPPUNIT_ASSERT_EQUAL(numMsgs, ecs->count());

  stage->stop();
}

void
SedaStageTest::testStartStop() {
  seda::Strategy::Ptr discard(new seda::DiscardStrategy());
  seda::EventCountStrategy::Ptr ecs(new seda::EventCountStrategy(discard));
  discard = seda::Strategy::Ptr(ecs);
  seda::Stage::Ptr stage(new seda::Stage("discard", discard, 2));

  const std::size_t numMsgs(10);
  
  stage->start();

  for (std::size_t i=0; i < numMsgs; ++i) {
    stage->send(seda::IEvent::Ptr(new seda::StringEvent("foo")));
  }
  stage->waitUntilEmpty(100);
  ecs->wait(numMsgs, 1000);
  
  CPPUNIT_ASSERT(stage->queue()->empty());
  CPPUNIT_ASSERT_EQUAL(numMsgs, ecs->count());

  stage->stop();

  ecs->reset();
  
  stage->start();
  for (std::size_t i=0; i < numMsgs; ++i) {
    stage->send(seda::IEvent::Ptr(new seda::StringEvent("bar")));
  }
  stage->waitUntilEmpty(100);
  ecs->wait(numMsgs, 1000);

  CPPUNIT_ASSERT(stage->queue()->empty());
  CPPUNIT_ASSERT_EQUAL(numMsgs, ecs->count());

  stage->stop();
}

void
SedaStageTest::testForwardEvents() {
  seda::Strategy::Ptr discard(new seda::DiscardStrategy());
  seda::EventCountStrategy::Ptr ecs(new seda::EventCountStrategy(discard));
  discard = seda::Strategy::Ptr(ecs);
  seda::Stage::Ptr final(new seda::Stage("final", discard, 2));

  seda::Strategy::Ptr fwdStrategy(new seda::ForwardStrategy("final"));
  seda::Stage::Ptr first(new seda::Stage("first", fwdStrategy));

  // register the stages
  StageRegistry::instance().insert(first);
  StageRegistry::instance().insert(final);
  
  first->start();
  final->start();

  const std::size_t numMsgs(5);
  for (std::size_t i=0; i < numMsgs; ++i) {
    first->send(seda::IEvent::Ptr(new seda::StringEvent("foo")));
  }

  first->waitUntilEmpty(100);
  final->waitUntilEmpty(100);
  ecs->wait(numMsgs, 1000);

  CPPUNIT_ASSERT(first->queue()->empty());
  CPPUNIT_ASSERT(final->queue()->empty());
  CPPUNIT_ASSERT_EQUAL(numMsgs, ecs->count());

  final->stop();
  first->stop();
}

void
SedaStageTest::testCompositeStrategy() {
  seda::Strategy::Ptr discard(new seda::DiscardStrategy());
  seda::EventCountStrategy::Ptr ecs(new seda::EventCountStrategy(discard));
  discard = seda::Strategy::Ptr(ecs);
  seda::Stage::Ptr final(new seda::Stage("discard", discard, 2));

  seda::CompositeStrategy::Ptr composite(new seda::CompositeStrategy("composite"));
  composite->add(seda::Strategy::Ptr(new seda::ForwardStrategy("discard")));
  composite->add(seda::Strategy::Ptr(new seda::ForwardStrategy("discard")));
  seda::Stage::Ptr first(new seda::Stage("fwd", composite));

  // register the stages
  StageRegistry::instance().insert(first);
  StageRegistry::instance().insert(final);

  first->start();
  final->start();

  first->send(seda::IEvent::Ptr(new seda::StringEvent("foo")));

  first->waitUntilEmpty(100);
  final->waitUntilEmpty(100);
  ecs->wait(2, 1000); // event should have been duplicated

  CPPUNIT_ASSERT(first->queue()->empty());
  CPPUNIT_ASSERT(final->queue()->empty());
  CPPUNIT_ASSERT_EQUAL((std::size_t)2, ecs->count());

  final->stop();
  first->stop();
}

void SedaStageTest::testAccumulateStrategy() {
  SEDA_LOG_DEBUG("Testing AccumulateStrategy");
  seda::AccumulateStrategy::Ptr accumulate(new seda::AccumulateStrategy("accumulate"));
  seda::EventCountStrategy::Ptr ecs(new seda::EventCountStrategy(accumulate));
  seda::Stage::Ptr first(new seda::Stage("accumulate", ecs));

  // register the stages
  StageRegistry::instance().insert(first);

  first->start();

  seda::IEvent::Ptr sendEvent(new seda::StringEvent("foo"));
  first->send(sendEvent);

  first->waitUntilEmpty(100);
  ecs->wait(1, 1000); 

  CPPUNIT_ASSERT(first->queue()->empty());
  CPPUNIT_ASSERT_EQUAL((std::size_t)1, ecs->count());
  
  // Now, check what we have accumulated in our strategy.
  SEDA_LOG_DEBUG("Expected event: " << sendEvent->str());
  seda::AccumulateStrategy::iterator_type it;
  for (it = accumulate->getIEventIteratorBegin(); it != accumulate->getIEventIteratorEnd(); *it++) {
    SEDA_LOG_DEBUG("Found event: " << (*it)->str());
    if ((*it)->str().compare(sendEvent->str()) != 0) 
      CPPUNIT_FAIL("Expected and actual event differ!");
  }

  first->stop();
}

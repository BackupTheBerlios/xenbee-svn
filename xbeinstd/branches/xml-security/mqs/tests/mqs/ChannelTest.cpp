#include <string>
#include <iostream>

#include <cms/TextMessage.h>
#include <mqs/BrokerURI.hpp>

#include "ChannelTest.hpp"
#include "testsconfig.hpp"

using namespace mqs::tests;

CPPUNIT_TEST_SUITE_REGISTRATION( ChannelTest );

ChannelTest::ChannelTest() : MQS_INIT_LOGGER("tests.mqs.channel"), _channel(0) {}

void ChannelTest::setUp() {
    MQS_LOG_DEBUG("setup");
}

void ChannelTest::tearDown() {
  //  _channel->stop();
  if (_channel)
    delete _channel;
  _channel = 0;
}

void ChannelTest::testStart_illegal_URI_Throws() {
  doStart("foo://blahblub:61617", "mqs.tests?type=queue");
}

void ChannelTest::testStartNoQueueServer_Throws() {
  doStart("tcp://127.0.0.1:56565", "mqs.tests?type=queue");
}

void ChannelTest::testStart_Timeout_Throws() {
  std::cerr << "I: testing connection timeout" << std::endl;
  doStart("tcp://localhost:61617?transport.ResponseCorrelator.maxResponseWaitTime=100", "mqs.tests?type=queue");
}

void ChannelTest::testSendReceiveSimple() {
  doStart(TEST_BROKER_URI, "mqs.test?type=queue");
  cms::TextMessage* msg = _channel->createTextMessage("hello world!");
  *_channel << msg;
  _channel->send(msg);
  delete msg;
  msg = dynamic_cast<cms::TextMessage*>(_channel->recv(1000));
  CPPUNIT_ASSERT_MESSAGE("received non-null message", msg != 0);
  CPPUNIT_ASSERT_EQUAL(std::string("hello world!"), msg->getText());
}

void ChannelTest::testSendReply() {
  doStart(TEST_BROKER_URI, "mqs.test?type=queue");
  cms::TextMessage* msg = _channel->createTextMessage("hello");
  std::string id = _channel->async_request(msg, mqs::Destination("mqs.test"));
  delete msg;
  msg = dynamic_cast<cms::TextMessage*>(_channel->recv(1000));
  CPPUNIT_ASSERT_MESSAGE("did not receive a message", msg != 0);
  CPPUNIT_ASSERT_EQUAL(std::string("hello"), msg->getText());
  _channel->reply(msg, "world!");
  delete msg;
  msg = dynamic_cast<cms::TextMessage*>(_channel->wait_reply(id, 1000));
  CPPUNIT_ASSERT_MESSAGE("did not receive a message", msg != 0);
  CPPUNIT_ASSERT_EQUAL(std::string("world!"), msg->getText());
}

void ChannelTest::testStartStopChannel() {
    MQS_LOG_INFO("starting the channel");
    
    // start the channel
    _channel = new mqs::Channel(mqs::BrokerURI(TEST_BROKER_URI), mqs::Destination("tests.mqs?type=queue"));
    CPPUNIT_ASSERT(!_channel->is_started());

    _channel->start();

    CPPUNIT_ASSERT_MESSAGE("channel could not be started", _channel->is_started());
    
    MQS_LOG_INFO("sending first message");

    // send a message
    cms::TextMessage* msg = _channel->createTextMessage("hello");
    _channel->send(msg);
    delete msg;
    msg = dynamic_cast<cms::TextMessage*>(_channel->recv(1000));
    CPPUNIT_ASSERT_MESSAGE("did not receive a message", msg != 0);

    MQS_LOG_INFO("stopping the channel");

    // stop the channel
    _channel->stop();
    CPPUNIT_ASSERT_MESSAGE("channel could not be stopped", (!_channel->is_started()));
    
    MQS_LOG_INFO("starting the channel again");
    // start it again
    _channel->start();

    MQS_LOG_INFO("sending second message");
    // send another message
    msg = _channel->createTextMessage("hello");
    _channel->send(msg);
    delete msg;
    msg = dynamic_cast<cms::TextMessage*>(_channel->recv(1000));
    CPPUNIT_ASSERT_MESSAGE("did not receive a message", msg != 0);
}

void ChannelTest::doStart(const std::string& uri, const std::string& q) {
  if (_channel) {
    _channel->stop();
    delete _channel;
  }
  _channel = new mqs::Channel(mqs::BrokerURI(uri), mqs::Destination(q));
  _channel->start();
}

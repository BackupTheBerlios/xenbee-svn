#include <string>
#include <iostream>

#include <cms/TextMessage.h>
#include <mqs/BrokerURI.hpp>

#include "ChannelTest.hpp"
#include "testsconfig.hpp"

using namespace mqs::tests;

CPPUNIT_TEST_SUITE_REGISTRATION( ChannelTest );

ChannelTest::ChannelTest() : MQS_INIT_LOGGER("tests.mqs.channel"), _channel(0), _awaitingException(false),_exceptionArrived(false) {}

void ChannelTest::setUp() {
    MQS_LOG_DEBUG("setup");
    _awaitingException = false;
    _exceptionArrived = false;
}

void ChannelTest::tearDown() {
    //  _channel->stop();
    if (_channel) {
        _channel->stop();
        delete _channel;
    }
    _channel = 0;
}

void ChannelTest::testStart_illegal_URI_Throws() {
    MQS_LOG_INFO("**** TEST: testStart_illegal_URI_Throws");

    doStart("foo://blahblub:61617", "mqs.tests?type=queue");
}

void ChannelTest::testStartNoQueueServer_Throws() {
    MQS_LOG_INFO("**** TEST: testStartNoQueueServer_Throws");

    doStart("tcp://127.0.0.1:56565", "mqs.tests?type=queue");
}

void ChannelTest::testStart_Timeout_Throws() {
    MQS_LOG_INFO("**** TEST: testStart_Timeout_Throws");

    std::cerr << "I: testing connection timeout" << std::endl;
    doStart("tcp://localhost:61617?transport.ResponseCorrelator.maxResponseWaitTime=100", "mqs.tests?type=queue");
}

void ChannelTest::testSendReceiveSimple() {
    MQS_LOG_INFO("**** TEST: testSendReceiveSimple");

    doStart("mqs.test?type=queue");
    cms::TextMessage* msg = _channel->createTextMessage("hello world!");
    *_channel << msg;
    _channel->send(msg);
    delete msg;
    msg = dynamic_cast<cms::TextMessage*>(_channel->recv(1000));
    CPPUNIT_ASSERT_MESSAGE("received non-null message", msg != 0);
    CPPUNIT_ASSERT_EQUAL(std::string("hello world!"), msg->getText());
    delete msg;
}

void ChannelTest::testSendReply() {
    MQS_LOG_INFO("**** TEST: testSendReply");

    doStart("mqs.test?type=queue");
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
    delete msg;
}

void ChannelTest::testStartStopChannel() {
    MQS_LOG_INFO("**** TEST: testStartStopChannel");

    MQS_LOG_INFO("starting the channel");

    // start the channel
    doStart("tests.mqs?type=queue");
    CPPUNIT_ASSERT_MESSAGE("channel could not be started", _channel->is_started());

    MQS_LOG_INFO("sending first message");

    // send a message
    cms::TextMessage* msg = _channel->createTextMessage("hello 1");
    _channel->send(msg);
    delete msg;
    msg = dynamic_cast<cms::TextMessage*>(_channel->recv(1000));
    CPPUNIT_ASSERT_MESSAGE("did not receive a message", msg != 0);
    CPPUNIT_ASSERT_EQUAL(std::string("hello 1"), msg->getText());
    delete msg;

    MQS_LOG_INFO("stopping the channel");

    // stop the channel
    _channel->stop();
    CPPUNIT_ASSERT_MESSAGE("channel could not be stopped", (!_channel->is_started()));

    MQS_LOG_INFO("starting the channel again");
    // start it again
    _channel->start(true);

    MQS_LOG_INFO("sending second message");
    // send another message
    msg = _channel->createTextMessage("hello 2");
    _channel->send(msg);
    delete msg;
    msg = dynamic_cast<cms::TextMessage*>(_channel->recv(1000));
    CPPUNIT_ASSERT_MESSAGE("did not receive a message", msg != 0);
    CPPUNIT_ASSERT_MESSAGE("message content differs", std::string("hello 2") == msg->getText());
    delete msg;
}

void ChannelTest::testAddDelIncomingQueue() {
    MQS_LOG_INFO("**** TEST: testAddDelIncomingQueue");

    std::string msg_id;
    MQS_LOG_WARN("sending messages with ttl != unlimited, since we get already received messages otherwise");

    // start the channel
    doStart("tests.mqs?type=queue");

    // send a message to the channel's queue
    msg_id = _channel->send("Hello World!", mqs::Destination("tests.mqs?type=queue&timeToLive=1000"), mqs::Destination("tests.mqs?type=queue"));
    {
        cms::TextMessage *msg(_channel->recv<cms::TextMessage>(1000));
        CPPUNIT_ASSERT_MESSAGE("did not receive a message", msg != 0);
        CPPUNIT_ASSERT_EQUAL(std::string("Hello World!"), msg->getText());
        CPPUNIT_ASSERT_EQUAL(msg_id, msg->getCMSMessageID());
        delete msg;
    }

    // remove the only incoming queue
    _channel->delIncomingQueue("tests.mqs?type=queue");

    // repeat the sending, no message should be received
    msg_id = _channel->send("Hello World!", "tests.mqs?type=queue&timeToLive=10000", "tests.mqs?type=queue");
    {
        cms::TextMessage *msg(_channel->recv<cms::TextMessage>(2000));
        if (msg) {
            delete msg;
            CPPUNIT_ASSERT_MESSAGE("received an unexpected message", false);
        }
    }

    // adding the queue again should result in a message
    _channel->addIncomingQueue("tests.mqs?type=queue");
    {
        cms::TextMessage *msg(_channel->recv<cms::TextMessage>(1000));
        CPPUNIT_ASSERT_MESSAGE("did not receive a message", msg != 0);
        CPPUNIT_ASSERT_EQUAL(msg_id, msg->getCMSMessageID());
        delete msg;
    }
}

void ChannelTest::testConnectionLoss() {
    MQS_LOG_INFO("think about a way how to check this automatically");
    doStart("tests.mqs?type=queue");
    _awaitingException=true;
    MQS_LOG_INFO("please kill the message-queue server now");
    sleep(10);
    if (_exceptionArrived) {
        MQS_LOG_INFO("please restart the message-queue server now");
        sleep(10);
    } else {
        CPPUNIT_ASSERT_MESSAGE("Expected exception did not occur during connection loss test", false);
    }
}

void ChannelTest::onException(const cms::CMSException &e) {
    MQS_LOG_WARN("think about a way how to check this automatically" << e.getMessage());
    _exceptionArrived = true;
}

void ChannelTest::doStart(const std::string &q) {
    doStart(TEST_BROKER_URI, q);
}
void ChannelTest::doStart(const char *q) {
    doStart(TEST_BROKER_URI, std::string(q));
}

void ChannelTest::doStart(const std::string& uri, const std::string& q) {
    if (_channel) {
        _channel->stop();
        delete _channel;
    }
    _channel = new mqs::Channel(mqs::BrokerURI(uri), mqs::Destination(q));
    _channel->setExceptionListener(this);
    _channel->start(true);
}


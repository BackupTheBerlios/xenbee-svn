#include <string>
#include <iostream>

#include <cms/TextMessage.h>
#include <cms/Message.h>
#include <cms/BytesMessage.h>
#include <activemq/exceptions/ActiveMQException.h>

#include <mqs/Message.hpp>
#include <mqs/BrokerURI.hpp>
#include <mqs/ChannelConnectionFailed.hpp>

#include "ChannelTest.hpp"
#include "testsconfig.hpp"

using namespace mqs::tests;

CPPUNIT_TEST_SUITE_REGISTRATION( ChannelTest );

ChannelTest::ChannelTest() : MQS_INIT_LOGGER("tests.mqs.channel"), _channel(0), _awaitingException(false),_exceptionArrived(false) {}

void ChannelTest::setUp() {
    MQS_LOG_DEBUG("setup");
    _awaitingException = false;
    _exceptionArrived = false;
    _channel = 0;
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

    try {
        doStart("foo://blahblub:61617", "tests.mqs?type=queue");
    } catch (const activemq::exceptions::ActiveMQException &e) {
        MQS_LOG_WARN("start failed: " << e.getMessage() << ": " << e.getStackTraceString());
    } catch (const cms::CMSException &e) {
        MQS_LOG_WARN("start failed: " << e.getMessage() << ": " << e.getStackTraceString());
    } 
}

void ChannelTest::testStartNoQueueServer() {
    MQS_LOG_INFO("**** TEST: testStartNoQueueServer_Throws");

    mqs::Channel::Ptr c(new mqs::Channel(mqs::BrokerURI("tcp://127.0.0.1:12345"), "tests.mqs"));
    try {
        c->start();
        CPPUNIT_ASSERT_MESSAGE("connection to 127.0.0.1:12345 succeeded, please make sure nothing listens there", false);
    } catch (const mqs::ChannelConnectionFailed &ex) {
        MQS_LOG_INFO("connection failed with reason: " << ex.what());
    } catch (const cms::CMSException &ex) {
        MQS_LOG_INFO("connection failed: " << ex.getMessage() << ": " << ex.getStackTraceString());
    } catch (const std::exception &ex) {
        MQS_LOG_INFO("connection failed: " << ex.what());
    } catch (...) {
        MQS_LOG_INFO("connection failed with an unknown reason");
    }
}

void ChannelTest::testStart_Timeout_Throws() {
    MQS_LOG_INFO("**** TEST: testStart_Timeout_Throws");

    std::cerr << "I: testing connection timeout" << std::endl;
    doStart("tcp://localhost:61617?transport.ResponseCorrelator.maxResponseWaitTime=100", "tests.mqs?type=queue");
}

void ChannelTest::testSendReceiveSimple() {
    MQS_LOG_INFO("**** TEST: testSendReceiveSimple");

    doStart("tests.mqs?type=queue");
    MQS_LOG_INFO("sending message");
    
    mqs::Message msg("hello world!", "tests.mqs", "tests.mqs");
    _channel->send(msg);
    MQS_LOG_INFO("message sent");
    MQS_LOG_INFO("waiting for message");
    mqs::Message::Ptr rmsg = _channel->recv(1000);

    CPPUNIT_ASSERT(rmsg.get() != NULL);
    //MQS_LOG_DEBUG("received message with body: " << rmsg->body());
    CPPUNIT_ASSERT_EQUAL(std::string("hello world!"), rmsg->body());
}

void ChannelTest::testSendReceiveLarge() {
    MQS_LOG_INFO("**** TEST: testSendReceiveLarge");

    doStart("tests.mqs?type=queue");
    MQS_LOG_INFO("sending message");
    
    char p[128*1024];
    unsigned int i=0, j=0;
    char z='0';
    p[i++] = '0';
    p[i++] = '0';
    p[i++] = z++;i++;
    
    do {
      p[i-1]= 'a'+(j%26);
      if(!((j+1)%26)) {
        p[i++] = '\n';
        p[i++] = '0';
        p[i++] = '0';
        p[i++] = z++;
        p[i++] = ':';
        if(z > '9') z='0';
      }
      
      i++;j++;
      
    }
    while (i <= sizeof(p));
    
    //for(unsigned int i=0; i < sizeof(p); i++) {
    //  p[i]= 'a'+(i%26);
    //  if(!(i%26)) p[i] = '\n';
    //}
    //memset(p, 'a', sizeof(p));
    std::string largeMessage(p, sizeof(p));

    mqs::Message msg(largeMessage, "tests.mqs", "tests.mqs");
    _channel->async_request(msg);
    //_channel->send(msg);
    MQS_LOG_INFO("message sent");
    MQS_LOG_INFO("waiting for message");
    mqs::Message::Ptr rmsg = _channel->recv(2000);

    CPPUNIT_ASSERT(rmsg.get() != NULL);
    MQS_LOG_DEBUG("received message with body: " << rmsg->body());
    CPPUNIT_ASSERT_EQUAL(largeMessage, rmsg->body());
}

void ChannelTest::testMessageId() {
    MQS_LOG_INFO("**** TEST: testMessageId");

    doStart("tests.mqs?type=queue");

    mqs::Message msg("hello world!", "tests.mqs", "tests.mqs");
    _channel->send(msg);

    MQS_LOG_INFO("message sent id:" << msg.id());
    mqs::Message::Ptr rmsg = _channel->recv(1000);

    CPPUNIT_ASSERT(rmsg.get() != NULL);
    CPPUNIT_ASSERT_EQUAL(msg.id(), rmsg->id());
}

void ChannelTest::testSendReply() {
    MQS_LOG_INFO("**** TEST: testSendReply");

    doStart("tests.mqs?type=queue");
    mqs::Message msg("hello", "tests.mqs", "tests.mqs");
    std::string id = _channel->async_request(msg);

    mqs::Message::Ptr rmsg(_channel->recv(1000));
    CPPUNIT_ASSERT_MESSAGE("did not receive a message", rmsg.get() != NULL);
    CPPUNIT_ASSERT_EQUAL(std::string("hello"), rmsg->body());
    mqs::Message r("world!", "tests.mqs", "tests.mqs");
    _channel->reply(*rmsg, r);

    mqs::Message::Ptr resp(_channel->wait_reply(id, 1000));
    CPPUNIT_ASSERT_MESSAGE("did not receive a response", resp.get() != NULL);
    CPPUNIT_ASSERT_EQUAL(std::string("world!"), resp->body());
}

void ChannelTest::testStartStopChannel() {
    MQS_LOG_INFO("**** TEST: testStartStopChannel");

    MQS_LOG_INFO("starting the channel");

    // start the channel
    doStart("tests.mqs?type=queue");
    CPPUNIT_ASSERT_MESSAGE("channel could not be started", _channel->is_started());

    // send a message
    MQS_LOG_INFO("sending first message");
    _channel->send(mqs::Message("hello 1", "tests.mqs", "tests.mqs"));

    // receive
    mqs::Message::Ptr msg1(_channel->recv(1000));

    CPPUNIT_ASSERT_MESSAGE("did not receive a message", msg1.get() != NULL);
    CPPUNIT_ASSERT_EQUAL(std::string("hello 1"), msg1->body());

    MQS_LOG_INFO("stopping the channel");

    // stop the channel
    _channel->stop();
    CPPUNIT_ASSERT_MESSAGE("channel could not be stopped", (!_channel->is_started()));

    MQS_LOG_INFO("starting the channel again");
    // start it again
    _channel->start(true);

    // send another message
    MQS_LOG_INFO("sending second message");
    _channel->send(mqs::Message("hello 2", "tests.mqs", "tests.mqs"));
    mqs::Message::Ptr msg2(_channel->recv(1000));

    CPPUNIT_ASSERT_MESSAGE("did not receive a message", msg2.get() != NULL);
    CPPUNIT_ASSERT_MESSAGE("message content differs", std::string("hello 2") == msg2->body());
}

void ChannelTest::testAddDelIncomingQueue() {
    MQS_LOG_INFO("**** TEST: testAddDelIncomingQueue");

    std::string msg_id;
    MQS_LOG_WARN("sending messages with ttl != unlimited, since we get already received messages otherwise");

    // start the channel
    doStart("tests.mqs?type=queue");

    // send a message to the channel's queue
    msg_id = _channel->send(mqs::Message("hello world!", "tests.mqs", "tests.mqs?timeToLive=1000"));
    {
        mqs::Message::Ptr msg(_channel->recv(1000));
        CPPUNIT_ASSERT_MESSAGE("did not receive a message", msg.get() != 0);
        CPPUNIT_ASSERT_EQUAL(std::string("hello world!"), msg->body());
        CPPUNIT_ASSERT_EQUAL(msg_id, msg->id());
    }

    // remove the only incoming queue
    MQS_LOG_DEBUG("removing incoming queue");
    _channel->delIncomingQueue("tests.mqs?type=queue");

    // repeat the sending, no message should be received
    msg_id = _channel->send(mqs::Message("hello world!", "tests.mqs", "tests.mqs?timeToLive=1000&deliveryMode=persistent"));
    {
        mqs::Message::Ptr msg(_channel->recv(1000));
        CPPUNIT_ASSERT_MESSAGE("received an unexpected message", msg.get() == 0);
    }

    // adding the queue again should result in a message
    MQS_LOG_DEBUG("adding incoming queue");
    _channel->addIncomingQueue("tests.mqs?type=queue");
    msg_id = _channel->send(mqs::Message("hello world!", "tests.mqs", "tests.mqs?timeToLive=1000&deliveryMode=persistent"));
    {
        MQS_LOG_DEBUG("trying to receive message");
        mqs::Message::Ptr msg(_channel->recv(1000));
        CPPUNIT_ASSERT_MESSAGE("did not receive a message", msg.get() != 0);
        CPPUNIT_ASSERT_EQUAL(std::string("hello world!"), msg->body());
        CPPUNIT_ASSERT_EQUAL(msg_id, msg->id());
    }
}

void ChannelTest::testConnectionLoss() {
    MQS_LOG_INFO("**** TEST: testConnectionLoss");

    mqs::Channel::Ptr c(new mqs::Channel(mqs::BrokerURI(TEST_BROKER_URI), "tests.mqs"));
    try {
        c->start();
        c->setExceptionListener(this);
    } catch (const mqs::ChannelConnectionFailed &ex) {
        MQS_LOG_INFO("connection failed with reason: " << ex.what());
        CPPUNIT_ASSERT_MESSAGE("could not connect to message queue server", false);
    } catch (const cms::CMSException &ex) {
        MQS_LOG_INFO("connection failed: " << ex.getMessage() << ": " << ex.getStackTraceString());
        CPPUNIT_ASSERT_MESSAGE("could not connect to message queue server", false);
    } catch (const std::exception &ex) {
        MQS_LOG_INFO("connection failed: " << ex.what());
        CPPUNIT_ASSERT_MESSAGE("could not connect to message queue server", false);
    } catch (...) {
        MQS_LOG_INFO("connection failed with an unknown reason");
        CPPUNIT_ASSERT_MESSAGE("could not connect to message queue server", false);
    }
 
    MQS_LOG_INFO("think about a way how to check this automatically");
    _awaitingException=true;
    for (size_t i = 0; i < 3; ++i) {
        if (_exceptionArrived) break;

        MQS_LOG_INFO("please kill the message-queue server now");
#if defined(WIN32)
        Sleep(10000);
#else
        sleep(10);
#endif
    }
    if (_exceptionArrived) {
        MQS_LOG_INFO("you may restart the message-queue server now");
#if defined(WIN32)
        Sleep(10000);
#else
        sleep(10);
#endif
    } else {
        CPPUNIT_ASSERT_MESSAGE("Expected exception did not occur during connection loss test", false);
    }
}

void ChannelTest::testMultipleSender() {
    MQS_LOG_INFO("*** executing test testMultipleSender");
    mqs::Channel::Ptr serverChannel(new mqs::Channel(mqs::BrokerURI(TEST_BROKER_URI),  "tests.mqs.server"));
    mqs::Channel::Ptr clientAChannel(new mqs::Channel(mqs::BrokerURI(TEST_BROKER_URI), "tests.mqs.client.a"));
    mqs::Channel::Ptr clientBChannel(new mqs::Channel(mqs::BrokerURI(TEST_BROKER_URI), "tests.mqs.client.b"));

    /*
    serverChannel->setExceptionListener(this);
    clientAChannel->setExceptionListener(this);
    clientBChannel->setExceptionListener(this);
    */

    /*
    serverChannel->username("guest");
    serverChannel->password("guest");
    clientAChannel->username("guest");
    clientAChannel->password("guest");
    clientBChannel->username("guest");
    clientBChannel->password("guest");
    */

    serverChannel->start(true);
    clientAChannel->start(true);
    clientBChannel->start(true);

    // send a message
    std::string idA = serverChannel->send(mqs::Message("hello A", "tests.mqs.server", "tests.mqs.client.a"));
    std::string idB = serverChannel->send(mqs::Message("hello B", "tests.mqs.server", "tests.mqs.client.b"));

    mqs::Message::Ptr msgA(clientAChannel->recv(5000));
    mqs::Message::Ptr msgB(clientBChannel->recv(5000));

    CPPUNIT_ASSERT(msgA.get() != 0);
    CPPUNIT_ASSERT_EQUAL(idA, msgA->id());
    CPPUNIT_ASSERT(msgB.get() != 0);
    CPPUNIT_ASSERT_EQUAL(idB, msgB->id());
}

void ChannelTest::onException(const cms::CMSException &e) {
    MQS_LOG_WARN("think about a way how to check for this automatically: " << e.getMessage());
    _exceptionArrived = true;
}
void ChannelTest::onException(const mqs::MQSException &e) {
    MQS_LOG_WARN("think about a way how to check this automatically: " << e.what());
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
    /*
    _channel->username("guest");
    _channel->password("guest");
    */
    _channel->start(true);
}


#include <iostream>
#include <sstream>

#include <mqs/Channel.hpp>
#include <mqs/Response.hpp>

// activemq includes
#include <cms/Connection.h>
#include <cms/Message.h>
#include <cms/TextMessage.h>
#include <cms/BytesMessage.h>
#include <cms/MessageProducer.h>
#include <cms/MessageConsumer.h>
#include <cms/Destination.h>
#include <cms/Queue.h>
#include <cms/Topic.h>
#include <cms/Session.h>
#include <activemq/core/ActiveMQConnectionFactory.h>

#if PERFORM_CHANNEL_IS_STARTED_CHECK
#define ENSURE_STARTED() ensure_started()
#else
#define ENSURE_STARTED()
#endif

using namespace mqs;
using namespace cms;
using namespace activemq::core;

Channel::Channel(const mqs::BrokerURI &broker, const mqs::Destination &inout)
    : MQS_INIT_LOGGER("mqs.channel"),
      _broker(broker),
      _inQueue(inout),
      _outQueue(inout),
      _messageListener(0),
      _exceptionListener(0),
      _started(false),
      _blocked_receivers(0),
      _state(DISCONNECTED)
{
  
}

Channel::Channel(const mqs::BrokerURI &broker, const mqs::Destination &in, const mqs::Destination &out)
    : MQS_INIT_LOGGER("mqs.channel"),
      _broker(broker),
      _inQueue(in),
      _outQueue(out),
      _messageListener(0),
      _started(false),
      _blocked_receivers(0),
      _state(DISCONNECTED)
{
  
}

Channel::~Channel() {
    try {
        stop();
    } catch (cms::CMSException& e) {
        MQS_LOG_ERROR("error during channel stop procedure: " << e.getStackTraceString());
    } catch (const std::exception& e) {
        MQS_LOG_ERROR("error during channel stop procedure: " << e.what());
    } catch (...) {
        MQS_LOG_ERROR("unknown error during channel stop procedure");
    }
}

void
Channel::start(bool doFlush) {
    boost::unique_lock<boost::recursive_mutex> lock(_mtx);

    if (_started)
        return;
  
    // Create a ConnectionFactory
    std::tr1::shared_ptr<ActiveMQConnectionFactory> connectionFactory(new ActiveMQConnectionFactory(_broker.value));
  
    // Create a Connection
    _connection.reset(connectionFactory->createConnection());

    _connection->setExceptionListener(this);
    _connection->start();
  
  
    // Create a Session
    _session.reset(_connection->createSession(Session::AUTO_ACKNOWLEDGE));

    // create producer parts
    if (_outQueue.isTopic()) {
        _producer_destination.reset(_session->createTopic(_outQueue.str()));
    } else {
        _producer_destination.reset(_session->createQueue(_outQueue.str()));
    }
    _producer.reset(_session->createProducer(_producer_destination.get()));
  
    std::string deliveryMode = _outQueue.getStringProperty("deliveryMode", "persistent");
    if (deliveryMode == "persistent") {
        _producer->setDeliveryMode(DeliveryMode::PERSISTENT);
    } else if (deliveryMode == "non-persistent") {
        _producer->setDeliveryMode(DeliveryMode::NON_PERSISTENT);
    } else {
        throw MQSException("invalid delivery mode: "+deliveryMode);
    }
    _producer->setDisableMessageID(_outQueue.getBooleanProperty("disableMessageID", false));
    _producer->setDisableMessageTimeStamp(_outQueue.getBooleanProperty("disableMessageTimeStamp", false));
    _producer->setPriority(_outQueue.getIntProperty("priority", 4));
    _producer->setTimeToLive(_outQueue.getLongLongProperty("timeToLive", 0));
  
    _started = true;
    _state = CONNECTED;
    addIncomingQueue(_inQueue);
    notify();

    if (doFlush) {
        flushMessages();
    }
}

void
Channel::stop() {
    boost::unique_lock<boost::recursive_mutex> lock(_mtx);

    while (!_consumer.empty()) {
        struct Consumer c = _consumer.front(); _consumer.pop_front();
        c.mqs_destination.reset();
        c.destination.reset();
        if (c.consumer) {
            c.consumer->setMessageListener( NULL );
            c.consumer->close();
            c.consumer.reset();
        }
    }

    _producer_destination.reset();
    _producer.reset();
    
    if (_session.get())
        _session->close();

    if (_connection.get())
        _connection->close();

    _session.reset();
    _connection.reset();

    _started = false;
    _state = DISCONNECTED;
    notify();
}

void
Channel::addIncomingQueue(const mqs::Destination &dst) {
    ENSURE_STARTED();

    MQS_LOG_DEBUG("adding incoming queue: " << dst.str());
  
    struct Consumer consumer;
    consumer.destination = dst.toCMSDestination(*_session);
    consumer.mqs_destination = std::tr1::shared_ptr<mqs::Destination>(new mqs::Destination(dst));
    consumer.consumer = std::tr1::shared_ptr<cms::MessageConsumer>(_session->createConsumer(consumer.destination.get()));
    consumer.consumer->setMessageListener(this);

    boost::unique_lock<boost::recursive_mutex> lock(_mtx);
    _consumer.push_back(consumer);
}

void
Channel::delIncomingQueue(const mqs::Destination &dst) {
    // removes all incoming queues with the same name and type, disregarding further options
    boost::unique_lock<boost::recursive_mutex> lock(_mtx);
    std::list<Consumer>::iterator it(_consumer.begin());
    while (it != _consumer.end()) {
        if (it->mqs_destination->name() == dst.name() and it->mqs_destination->type() == dst.type()) {
            // found a match, remove it
            struct Consumer c(*it); it = _consumer.erase(it);
            c.mqs_destination.reset();
            c.destination.reset();
            if (c.consumer) {
                c.consumer->setMessageListener( NULL );
                c.consumer.reset();
            }
            MQS_LOG_DEBUG("removed incoming queue: " << dst.name());
        } else {
            ++it;
        }
    }
}

std::string
Channel::send(const std::string &text, const mqs::Destination &dst) {
    ENSURE_STARTED();

    MessagePtr msg(createTextMessage(text));
    send(msg.get(), dst);
    return msg->getCMSMessageID();
}

std::string
Channel::send(const std::string &text, const mqs::Destination &dst, const mqs::Destination &replyTo) {
    ENSURE_STARTED();

    MessagePtr msg(createTextMessage(text));
    send(msg.get(), dst, replyTo);
    return msg->getCMSMessageID();
}

std::string
Channel::send(Message *msg, const mqs::Destination &dst, const mqs::Destination &replyTo) {
    std::tr1::shared_ptr<cms::Destination> d(replyTo.toCMSDestination(*_session));
    msg->setCMSReplyTo(d.get());
    return send(msg, dst);
}

std::string
Channel::send(Message *msg, const mqs::Destination &dst) {
    ENSURE_STARTED();

    int deliveryMode;
    int priority;
    long long timeToLive;
  
    if (dst.hasProperty("deliveryMode")) {
        std::string specifiedDeliveryMode = dst.getStringProperty("deliveryMode");
        if (specifiedDeliveryMode == "persistent") {
            deliveryMode = cms::DeliveryMode::PERSISTENT;
        } else if (specifiedDeliveryMode == "non-persistent") {
            deliveryMode = cms::DeliveryMode::NON_PERSISTENT;
        } else {
            throw std::invalid_argument("invalid delivery mode: "+specifiedDeliveryMode);
        }
    } else {
        deliveryMode = _producer->getDeliveryMode();
    }
  
    priority = dst.hasProperty("priority") ? dst.getIntProperty("priority") : _producer->getPriority();
    timeToLive = dst.hasProperty("timeToLive") ? dst.getLongLongProperty("timeToLive") : _producer->getTimeToLive();

    std::tr1::shared_ptr<cms::Destination> d(dst.toCMSDestination(*_session));
    return send(msg, d.get(), deliveryMode, priority, timeToLive);
}

std::string
Channel::send(Message *msg) {
    ENSURE_STARTED();

    return send(msg, _producer_destination.get(), _producer->getDeliveryMode(), _producer->getPriority(), _producer->getTimeToLive());
}

std::string
Channel::send(Message *msg, const cms::Destination *d, int deliveryMode, int priority, long long timeToLive) {
    ENSURE_STARTED();
    
    _producer->send(d, msg, deliveryMode, priority, timeToLive);
    MQS_LOG_DEBUG("sent message"
                  << " id:"   << msg->getCMSMessageID()
                  << " mode:" << ((deliveryMode == cms::DeliveryMode::PERSISTENT) ? "persistent" : "non-persistent")
                  << " reply-to:" << mqs::Destination(msg->getCMSReplyTo()).str()
                  << " prio:" << priority
                  << " ttl:"  << timeToLive
                  << " corr:" << msg->getCMSCorrelationID()
                  << " type:" << msg->getCMSType());
    return msg->getCMSMessageID();
}

Message*
Channel::request(const std::string &text, const mqs::Destination &dst, unsigned long millisecs) {
    ENSURE_STARTED();

    MessagePtr m(createTextMessage(text));
    return request(m.get(), dst, millisecs);
}

Message*
Channel::request(Message *msg, const mqs::Destination &dst, unsigned long millisecs) {
    ENSURE_STARTED();

    const std::string requestID = async_request(msg, dst);
    return wait_reply(requestID, millisecs);
}

Message*
Channel::request(const std::string &text, unsigned long millisecs) {
    ENSURE_STARTED();

    return request(text, _outQueue, millisecs);
}

std::string
Channel::reply(const Message *msg, const std::string &text) {
    ENSURE_STARTED();

    MessagePtr r(createTextMessage(text));
    return reply(msg, r.get());
}

std::string
Channel::reply(const Message *msg, Message *r) {
    ENSURE_STARTED();

    if (msg->getCMSReplyTo() == 0) {
        throw std::invalid_argument("cannot reply to a message that does not have a reply-to field");
    }
    r->setCMSCorrelationID(msg->getCMSMessageID());
    MQS_LOG_DEBUG("replying to msg: " << msg->getCMSMessageID());
    return send(r, msg->getCMSReplyTo(), _producer->getDeliveryMode(), _producer->getPriority(), _producer->getTimeToLive());
}

std::string
Channel::async_request(const std::string &text, const mqs::Destination &dst) {
    ENSURE_STARTED();

    MessagePtr m(createTextMessage(text));
    return async_request(m.get(), dst);
}

std::string
Channel::async_request(Message *msg, const mqs::Destination &dst) {
    ENSURE_STARTED();

    std::string msg_id;
    {
        boost::unique_lock<boost::recursive_mutex> lk(_mtx);
        msg->setCMSReplyTo(_consumer.front().destination.get());
        MQS_LOG_DEBUG("sending async request to " << dst.str());
        msg_id = send(msg, dst);
        assert(!msg_id.empty());
     }
 
    // create a response object and put it into the queue (deleted in wait_reply)
    mqs::Response* response = new Response(msg_id);
    boost::unique_lock<boost::mutex> lock(_awaitingResponseMtx);
    _awaitingResponse.push_back(response);
  
    return msg_id;
}

Message*
Channel::wait_reply(const std::string &requestID, unsigned long millisecs) {
    ENSURE_STARTED();

    MQS_LOG_DEBUG("waiting for reply to: " << requestID);
    _awaitingResponseMtx.lock();
    // look for the matching response object
    std::vector<mqs::Response*>::iterator it = _awaitingResponse.begin();
    mqs::Response *response(0);
    for (; it != _awaitingResponse.end(); it++) {
        if ((*it)->getCorrelationID() == requestID) {
            // found the response object
            response = (*it);
            _awaitingResponseMtx.unlock();
            response->await(millisecs);
            break;
        }
    }
    if (response == 0) {
        _awaitingResponseMtx.unlock();
    } else {
        // remove the response object (iterator position might have changed...)
        _awaitingResponseMtx.lock();
        for (it = _awaitingResponse.begin(); it != _awaitingResponse.end(); it++) {
            if ((*it)->getCorrelationID() == requestID) {
                // found the response object
                _awaitingResponse.erase(it);
                break;
            }
        }
        _awaitingResponseMtx.unlock();
    }

    if (response) {
        Message *reply(response->getResponse());
        delete response;
        return reply;
    } else {
        MQS_LOG_FATAL("Inconsistent state: wait for reply did not find response object!");
        assert(false);
    }
}

Message*
Channel::createMessage() const {
    ENSURE_STARTED();

    return _session->createMessage();
}

TextMessage*
Channel::createTextMessage(const std::string &text) const {
    ENSURE_STARTED();

    return _session->createTextMessage(text);
}

BytesMessage*
Channel::createBytesMessage(const unsigned char *bytes, std::size_t length) const {
    ENSURE_STARTED();

    return _session->createBytesMessage(bytes, length);
}

void
Channel::setMessageListener(cms::MessageListener *listener) {
    boost::unique_lock<boost::recursive_mutex> lock(_mtx);
    _messageListener = listener;
}

void
Channel::setExceptionListener(cms::ExceptionListener *listener) {
    boost::unique_lock<boost::recursive_mutex> lock(_mtx);
    _exceptionListener = listener;
}

void
Channel::onMessage(const cms::Message *msg) {
    // handle incoming messages

    MQS_LOG_DEBUG("got new message: " << msg->getCMSMessageID());
  
    // 1. check for a thread waiting for a response
    {
        const std::string correlationID = msg->getCMSCorrelationID();
        if (!correlationID.empty()) {
            boost::unique_lock<boost::mutex> lock(_awaitingResponseMtx);
            MQS_LOG_DEBUG("message correlates to: " << correlationID);
            std::vector<mqs::Response*>::iterator it = _awaitingResponse.begin();
            for (; it != _awaitingResponse.end(); it++) {
                if ((*it)->getCorrelationID() == correlationID) {
                    // got a response, clone the message and notify the blocked thread
                    cms::Message* clonedMsg = msg->clone();
                    (*it)->setResponse(clonedMsg);
                    return;
                }
            }

            // got a response to some message, but no thread is waiting for one!!!
            MQS_LOG_WARN("got response to some message but noone is waiting!");
            return; // discard the message
        }
    }

    // if  we have  a message  listener registered,  let him  handle all
    // incoming messages unless there are blocked receivers
    if (_messageListener && !_blocked_receivers) {
        MQS_LOG_DEBUG("dispatching message to message listener");
        try {
            _messageListener->onMessage(msg);
        } catch(const std::exception& ex) {
            MQS_LOG_WARN("message handling failed: " << ex.what());
        } catch(...) {
            MQS_LOG_WARN("message handling failed: unknown error");
        }
    } else {
        boost::unique_lock<boost::mutex> lock(_incomingMessagesMutex);
        MQS_LOG_DEBUG("enqueueing message");
        cms::Message* clonedMsg = msg->clone();
        _incomingMessages.push_back(clonedMsg);
        _incomingMessagesCondition.notify_one();
    }
}

Message*
Channel::recv(unsigned long millis) {
    boost::unique_lock<boost::mutex> lock(_incomingMessagesMutex);
    _blocked_receivers++;
    // wait until a message is available
    while(_incomingMessages.empty()) {
        MQS_LOG_DEBUG("waiting for new messages");
        boost::system_time const timeout=boost::get_system_time() + boost::posix_time::milliseconds(millis);
        if (!_incomingMessagesCondition.timed_wait(lock, timeout))
            break;
    }
    if (_incomingMessages.empty()) {
        MQS_LOG_DEBUG("message waiting timed out");
        _blocked_receivers--;
        return 0;
    } else {
        Message* msg(_incomingMessages.front()); _incomingMessages.pop_front();
        MQS_LOG_DEBUG("received message: " << msg->getCMSMessageID());
        _blocked_receivers--;
        return msg;
    }
}

std::size_t
Channel::flushMessages() {
    MQS_LOG_DEBUG("flushing old messages...");
    std::size_t count(0);
    for (;;) {
        Message *m = recv(1000);
        if (m) {
            MQS_LOG_DEBUG("flushed message ("<< m->getCMSMessageID() <<")...");
            count++;
            delete m;
        } else {
            break;
        }
    }
    return count;
}

void
Channel::onException(const cms::CMSException &ex) {
    if (_exceptionListener) {
        try {
            _exceptionListener->onException(ex);
        } catch(...) {
            MQS_LOG_WARN("registered exception handler threw exception, discarding it!");
        }
    } else {
        MQS_LOG_WARN("no message listener registered to handle: " << ex.getMessage() << " " << ex.getStackTraceString());
    }
}

bool
Channel::is_started() const {
    return _started;
}

void
Channel::ensure_started() const throw(ChannelNotStarted) {
    if (! is_started())
        throw ChannelNotStarted();
}

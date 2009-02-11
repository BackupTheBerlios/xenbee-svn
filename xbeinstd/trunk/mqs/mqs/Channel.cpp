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
//using namespace cms;
using namespace activemq::core;

Channel::Channel(const mqs::BrokerURI &broker, const mqs::Destination &inout)
    : MQS_INIT_LOGGER(std::string("mqs.channel-") + inout.name()),
      _broker(broker),
      _inQueue(inout),
      _outQueue(inout),
      _msgSeqGen(mqs::MessageSequenceGenerator::newInstance()),
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
      _msgSeqGen(mqs::MessageSequenceGenerator::newInstance()),
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
  
    MQS_LOG_DEBUG("creating connection");
    _connection.reset(connectionFactory->createConnection());

    _connection->setExceptionListener(this);
    MQS_LOG_DEBUG("starting underlying connection");
    _connection->start();
  
  
    // Create a Session
    _session.reset(_connection->createSession(cms::Session::AUTO_ACKNOWLEDGE));

    // create producer parts
    if (_outQueue.isTopic()) {
        _producer_destination.reset(_session->createTopic(_outQueue.str()));
    } else {
        _producer_destination.reset(_session->createQueue(_outQueue.str()));
    }
    _producer.reset(_session->createProducer(_producer_destination.get()));
  
    std::string deliveryMode = _outQueue.getStringProperty("deliveryMode", "non-persistent");
    if (deliveryMode == "persistent") {
        _producer->setDeliveryMode(cms::DeliveryMode::PERSISTENT);
    } else if (deliveryMode == "non-persistent") {
        _producer->setDeliveryMode(cms::DeliveryMode::NON_PERSISTENT);
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

const std::string&
Channel::send(const mqs::Message &msg) {
    ENSURE_STARTED();

    std::tr1::shared_ptr<cms::Message> m(_session->createBytesMessage((unsigned char*)msg.body().c_str(), msg.body().size()));
    std::tr1::shared_ptr<cms::Destination> to(msg.to().toCMSDestination(*_session));
    std::tr1::shared_ptr<cms::Destination> from(msg.from().toCMSDestination(*_session));

    if (msg.id().empty()) {
        mqs::Message &m(const_cast<mqs::Message&>(msg));
        m.id(_msgSeqGen->next());
    }

    m->setCMSCorrelationID(msg.correlation());
    m->setCMSReplyTo(from.get()); 

    /* work around stomp */
    m->setStringProperty("amqp-message-id", msg.id());

    _producer->send(to.get(), m.get(), msg.deliveryMode(), msg.priority(), msg.ttl());

    MQS_LOG_DEBUG("sent message"
                  << " id:"       << msg.id()
                  << " mode:"     << ((msg.deliveryMode() == cms::DeliveryMode::PERSISTENT) ? "persistent" : "non-persistent")
                  << " reply-to:" << msg.from().str()
                  << " prio:"     << msg.priority()
                  << " ttl:"      << msg.ttl()
                  << " corr:"     << msg.correlation()
    );
     
    return msg.id();
}

mqs::Message::Ptr
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
        return mqs::Message::Ptr((mqs::Message*)NULL);
    } else {
        mqs::Message::Ptr msg(_incomingMessages.front()); _incomingMessages.pop_front();
        MQS_LOG_DEBUG("received message: " << msg->id());
        _blocked_receivers--;
        return msg;
    }
}

mqs::Message::Ptr
Channel::request(mqs::Message &msg, unsigned long millisecs) {
    ENSURE_STARTED();
    return wait_reply(async_request(msg), millisecs);
}

void
Channel::reply(const mqs::Message &msg, mqs::Message &rmsg) {
    ENSURE_STARTED();

    if (! msg.from().isValid()) {
        throw std::invalid_argument("cannot reply to a message that does not have a reply-to field");
    }

    rmsg.to(msg.from());
    rmsg.correlation(msg.id());
    MQS_LOG_DEBUG("replying to msg: " << msg.id());
    send(rmsg);
}

std::string
Channel::async_request(mqs::Message &msg) {
    ENSURE_STARTED();

    MQS_LOG_DEBUG("sending async request to " << msg.to().str());
    std::string msg_id = send(msg);
 
    // create a response object and put it into the queue (deleted in wait_reply)
    mqs::Response* response = new Response(msg_id);

    boost::unique_lock<boost::mutex> lock(_awaitingResponseMtx);
    _awaitingResponse.push_back(response);
  
    return msg_id;
}

mqs::Message::Ptr
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
        mqs::Message::Ptr reply(response->getResponse());
        delete response;
        return reply;
    } else {
        MQS_LOG_FATAL("Inconsistent state: wait for reply did not find response object!");
        abort();
    }
}

mqs::Message::Ptr
Channel::buildMessage(const cms::Message *cm) const {
    std::string body;

    cms::Message *m = const_cast<cms::Message*>(cm);
    if (cms::BytesMessage *bm = dynamic_cast<cms::BytesMessage*>(m)) {
        MQS_LOG_DEBUG("got a new bytes-message");
        body = std::string((char*)bm->getBodyBytes(), bm->getBodyLength());
    } else if (cms::TextMessage *tm = dynamic_cast<cms::TextMessage*>(m)) {
        MQS_LOG_DEBUG("got a new text-message");
        body = tm->getText();
    } else {
        throw MQSException("message not understood - must be TextMessage or BytesMessage");
    }
    mqs::Message::Ptr msg(new mqs::Message(body,
                mqs::Destination(m->getCMSReplyTo()),
                mqs::Destination(m->getCMSDestination())));
    if (m->propertyExists("amqp-message-id")) {
        msg->id(m->getStringProperty("amqp-message-id"));
    } else {
        msg->id(m->getCMSMessageID());
    }
    msg->correlation(m->getCMSCorrelationID());
    msg->ttl(m->getCMSExpiration());
    msg->priority(m->getCMSPriority());
    msg->deliveryMode(m->getCMSDeliveryMode());

    return msg;
}

void
Channel::setMessageListener(mqs::MessageListener *listener) {
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
    try {
        mqs::Message::Ptr m(buildMessage(msg));
        MQS_LOG_DEBUG("got new message: " << m->id());
  
        // 1. check for a thread waiting for a response
        {
            const std::string correlationID = m->correlation();
            if (! correlationID.empty()) {
                boost::unique_lock<boost::mutex> lock(_awaitingResponseMtx);
                MQS_LOG_DEBUG("message correlates to: " << correlationID);
                std::vector<mqs::Response*>::iterator it = _awaitingResponse.begin();
                for (; it != _awaitingResponse.end(); it++) {
                    if ((*it)->getCorrelationID() == correlationID) {
                        (*it)->setResponse(m);
                        return;
                    }
                }
                // got a response to some message, but no thread is waiting for one!!!
                MQS_LOG_WARN("got response to some message but noone is waiting!");
//                return; // discard the message
            }
        }

        // if  we have  a message  listener registered,  let him  handle all
        // incoming messages unless there are blocked receivers
        if (_messageListener && (_blocked_receivers == 0)) {
            MQS_LOG_DEBUG("dispatching message to message listener");
            try {
                _messageListener->onMessage(m);
            } catch(const std::exception& ex) {
                MQS_LOG_WARN("message handling failed: " << ex.what());
            } catch(...) {
                MQS_LOG_WARN("message handling failed: unknown error");
            }
        } else {
            boost::unique_lock<boost::mutex> lock(_incomingMessagesMutex);
            MQS_LOG_DEBUG("enqueueing message");
            _incomingMessages.push_back(m);
            _incomingMessagesCondition.notify_one();
        }
    } catch (const std::exception &ex) {
        MQS_LOG_ERROR("onMessage() failed: " << ex.what());
    }
}

std::size_t
Channel::flushMessages() {
    MQS_LOG_DEBUG("flushing old messages...");
    std::size_t count(0);
    for (;;) {
        mqs::Message::Ptr m(recv(1000));
        if (m) {
            MQS_LOG_DEBUG("flushed message ("<< m->id() <<")...");
            count++;
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

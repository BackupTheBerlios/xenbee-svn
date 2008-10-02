#ifndef MQS_CHANNEL_HPP
#define MQS_CHANNEL_HPP

#include <mqs/common.hpp>

#include <vector>
#include <list>
#include <tr1/memory>

#include <activemq/concurrent/Mutex.h>
#include <cms/ExceptionListener.h>
#include <cms/DeliveryMode.h>
#include <cms/Message.h>
#include <cms/TextMessage.h>
#include <cms/BytesMessage.h>
#include <cms/MessageListener.h>
#include <mqs/Destination.hpp>
#include <mqs/BrokerURI.hpp>
#include <mqs/MQSException.hpp>
#include <mqs/Observable.hpp>

// forward declarations
namespace cms {
    class Connection;
    class Session;
    class MessageProducer;
    class MessageConsumer;
    class Destination;
}

namespace mqs {
    typedef std::tr1::shared_ptr<cms::Message> MessagePtr;
    typedef std::tr1::shared_ptr<cms::TextMessage> TextMessagePtr;
    typedef std::tr1::shared_ptr<cms::BytesMessage> BytesMessagePtr;
  
    class Response;

    class ChannelNotStarted : public MQSException {
    public:
        ChannelNotStarted() : MQSException("channel not started yet") {}
        virtual ~ChannelNotStarted() throw () {}
    };
    
    class Channel : public cms::MessageListener,
                    public cms::ExceptionListener,
                    public mqs::Observable {
    public:
        typedef std::tr1::shared_ptr<Channel> Ptr;

        enum State {
            DISCONNECTED,
            CONNECTED
        };

        /**
           Create a new channel with the given broker uri.

           @param broker the broker to connect to
           @param srcdst the name outgoing messages are adressed to and on which message bus should be listened
        */
        Channel(const mqs::BrokerURI&, const mqs::Destination& srcdst);

        /**
           Create a new channel with the given broker uri.

           @param broker the broker to connect to
           @param src the name of the incoming message queue/topic
           @param dst the name outgoing messages are adressed to
        */
        Channel(const mqs::BrokerURI&, const mqs::Destination& src, const mqs::Destination& dst);
        virtual ~Channel();

        /**
           Start the channel and its underlying components.
        */
        void start(bool doFlush=false);

        /**
           Returns true iff the channel has been started, false otherwise.
         */
        bool is_started() const;

        State state() const {
            return _state;
        }
        
        /**
           Stops the channel
        */
        void stop();

        /**
           Place a request via the message broker.

           This function  effectively sends  the message via  the broker
           and waits  for a reply.  Depending on  the specified timeout,
           the calling process is blocked forever (timeout == -1) or (at
           most)  the  specified  duration.   The return  value  is  the
           received  message or  a null  pointer. The  ownership  of the
           returned message is the calling process.

           @param message the message to be sent
           @param dst the destination to send the message to
           @param timeout specifies how long to wait for a reply (milliseconds)
           @return cms::Message pointer to the reply or NULL
        */
        cms::Message* request(cms::Message* msg, const mqs::Destination& dst, unsigned long millisecs = INFINITE_WAITTIME);

        /**
           Convenience function for request(cms::Message).

           The   given  string   message  is   simply  wrapped   into  a
           cms::TextMessage.

           @see request(cms::Message*, mqs::Destination, long long)
        */
        cms::Message* request(const std::string& msg, const mqs::Destination& dst, unsigned long millisecs = INFINITE_WAITTIME);
        cms::Message* request(const std::string& msg, unsigned long millisecs = INFINITE_WAITTIME);

        /**
           Place an asynchronous request.

           The message  is sent asynchronously and  the function returns
           imediately with an identifier for the request.

           @param msg the request to be sent
           @return std::string an id that uniquely identifies the request
        */
        std::string async_request(cms::Message* msg, const Destination& dst);
        std::string async_request(const std::string& msg, const Destination& dst);

        /**
           Waits for a reply on a previously placed request message.

           Timeout specifies the number of milliseconds to wait before a
           NULL  pointer is returned.   If timeout  equals 0,  the call
           blocks indefinitely long.

           @param requestID the unique identifier for a request
           @param timeout number of milliseconds to wait or 0 for infinity
        */
        cms::Message* wait_reply(const std::string& requestID, unsigned long millisecs = INFINITE_WAITTIME);

        /**
           Send (and forget) a pregenerated message.

           @param msg the message to be sent
        */
        std::string send(const std::string& msg) { return send(msg, _outQueue); }
        std::string send(const std::string& msg, const mqs::Destination& dst);
        std::string send(const std::string& msg, const mqs::Destination& dst, const mqs::Destination& replyTo);
        std::string send(cms::Message* msg);
        std::string send(cms::Message* msg, const mqs::Destination& dst);
        std::string send(cms::Message* msg, const mqs::Destination& dst, const mqs::Destination& replyTo);

        Channel& operator<<(const std::string& msg) { send(msg); return *this; }
        Channel& operator<<(cms::Message* msg) { send(msg); return *this; }
    
        /**
           Reply to a received message.

           @param msg orginal message
           @param reply the reply message
        */
        std::string reply(const cms::Message* msg, cms::Message* reply);
        std::string reply(const cms::Message* msg, const std::string& reply);
    
        /**
           Receive the next new message.

           @param timeout wait for timeout milliseconds
           @return the message or NULL
        */
        cms::Message* recv(unsigned long millisecs = INFINITE_WAITTIME);
        template <class T> T* recv(unsigned long millisecs = INFINITE_WAITTIME) {
            cms::Message *m(recv(millisecs));
            T *t_msg(dynamic_cast<T*>(m));
            if (t_msg) {
                return t_msg;
            } else {
                if (m) {
                    MQS_LOG_WARN("recv could not dynamic_cast<...> the received message");
                    delete m; m = 0;
                }
                return 0;
            }
        }

        /**
           Asynchronously handle new messages.

           Note: The message listener only receives a new message, if no
           other process awaits  a message. That means, if  a process is
           waiting for  a reply  to a request,  he has control  over the
           incoming messages.

           @param listener the new message listener to use, specify NULL
           to remove any listener
        */
        void setMessageListener(cms::MessageListener* listener);

        void setExceptionListener(cms::ExceptionListener* listener);
      
        /******************************
         *                            *
         * Message creation functions *
         *                            *
         ******************************/
        cms::Message* createMessage() const;
        cms::TextMessage* createTextMessage(const std::string& body = "") const;
        cms::BytesMessage* createBytesMessage(const unsigned char* bytes = 0, std::size_t = 0) const;

        void addIncomingQueue(const mqs::Destination& dst);
        void delIncomingQueue(const mqs::Destination& dst);

        /**
           Removes all messages from the incoming queue.
       
        */
        std::size_t flushMessages();
    public:
        /**
           Implementation for the MessageListener interface.

           Enques a new incoming message.

           The intention behind this function is as follows:
           1. acquire lock of the awaiting response queue
           2. scan the response objects and look for a thread waiting for this response
           3. if object found:
             3a. set message as response
             3b. release lock and return
           4. release response mutex
           5. dispatch message:
             5a. if listener is registered let him handle the message
                 delete message
             5b. if no listener is registered:
               5b1: acquire lock
               5b2: push_back the message
               5b3: notify a potential receiver (blocked in recv)
               5b4: release lock
        */
        void onMessage(const cms::Message*);

        void onException(const cms::CMSException&);

    private:
        std::string send(cms::Message* msg, const cms::Destination* dst, int deliveryMode, int priority, long long timeToLive);
        void ensure_started() const throw (ChannelNotStarted);
    
        MQS_DECLARE_LOGGER();
        activemq::concurrent::Mutex _mtx;
    
        mqs::BrokerURI _broker;
        mqs::Destination _inQueue;
        mqs::Destination _outQueue;
    
        std::tr1::shared_ptr<cms::Connection> _connection;
        std::tr1::shared_ptr<cms::Session> _session;
        std::tr1::shared_ptr<cms::MessageProducer> _producer;
        std::tr1::shared_ptr<cms::Destination> _producer_destination;

        activemq::concurrent::Mutex _consumerMtx;
        struct Consumer {
            std::tr1::shared_ptr<mqs::Destination> mqs_destination;
            std::tr1::shared_ptr<cms::Destination> destination;
            std::tr1::shared_ptr<cms::MessageConsumer> consumer;
        };
        std::list<Consumer> _consumer;

        cms::MessageListener* _messageListener;
        cms::ExceptionListener* _exceptionListener;

        activemq::concurrent::Mutex _incomingMessagesMtx;
        std::list<cms::Message*> _incomingMessages;
    
        activemq::concurrent::Mutex _awaitingResponseMtx;
        std::vector<mqs::Response*> _awaitingResponse;

        // internal state keeper
        bool _started;
        std::size_t _blocked_receivers;
        State _state;
    };
}

#endif // !MQS_CHANNEL_HPP

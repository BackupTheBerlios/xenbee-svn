#ifndef MQS_CHANNEL_HPP
#define MQS_CHANNEL_HPP

#include <mqs/common.hpp>
#include <mqs/memory.hpp>

#include <vector>
#include <list>

#include <boost/thread.hpp>

#include <cms/ExceptionListener.h>
#include <cms/DeliveryMode.h>
#include <cms/Message.h>
#include <cms/MessageListener.h>

#include <mqs/Destination.hpp>
#include <mqs/BrokerURI.hpp>
#include <mqs/MQSException.hpp>
#include <mqs/ChannelNotStarted.hpp>
#include <mqs/ChannelConnectionFailed.hpp>
#include <mqs/Observable.hpp>
#include <mqs/Message.hpp>
#include <mqs/ExceptionListener.hpp>
#include <mqs/MessageListener.hpp>
#include <mqs/MessageSequenceGenerator.hpp>

// forward declarations
namespace cms {
    class Connection;
    class Session;
    class MessageProducer;
    class MessageConsumer;
    class Destination;
}

namespace mqs {
    class Response;

    class Channel : public cms::MessageListener,
                    public cms::ExceptionListener,
                    public mqs::Observable {
    public:
        typedef shared_ptr<Channel> Ptr;

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
        void start(bool doFlush=false) throw(ChannelConnectionFailed);

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
           @param timeout specifies how long to wait for a reply (milliseconds)
           @return mqs::Message pointer to the reply or NULL
        */
        mqs::Message::Ptr request(mqs::Message &msg, unsigned long millisecs);

        /**
           Place an asynchronous request.

           The message  is sent asynchronously and  the function returns
           imediately with an identifier for the request.

           @param msg the request to be sent
           @return std::string an id that uniquely identifies the request
        */
        std::string async_request(mqs::Message &msg);

        /**
           Reply to a received message.

           @param msg orginal message
           @param reply the reply message
        */
        void reply(const mqs::Message &msg, mqs::Message &reply);

        /**
           Waits for a reply on a previously placed request message.

           Timeout specifies the number of milliseconds to wait before a
           NULL  pointer is returned.   If timeout  equals 0,  the call
           blocks indefinitely long.

           @param requestID the unique identifier for a request
           @param timeout number of milliseconds to wait or 0 for infinity
        */
        mqs::Message::Ptr wait_reply(const std::string &requestID, unsigned long millisecs);

        /**
         * Send the given message.
         *
         * @param msg the message to be sent
         * @return the message id
         */
        const std::string &send(const mqs::Message &msg);

        /**
           Receive the next new message.

           @param timeout wait for timeout milliseconds
           @return a pointer to the received message (maybe 0)
        */
        mqs::Message::Ptr recv(unsigned long millisecs);

        Channel& operator<<(mqs::Message &msg) { send(msg); return *this; }
    
        /**
           Asynchronously handle new messages.

           Note: The message listener only receives a new message, if no
           other process awaits  a message. That means, if  a process is
           waiting for  a reply  to a request,  he has control  over the
           incoming messages.

           @param listener the new message listener to use, specify NULL
           to remove any listener
        */
        void setMessageListener(mqs::MessageListener* listener);
        void setExceptionListener(mqs::ExceptionListener* listener);
      
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
        void ensure_started() const throw (ChannelNotStarted);
        mqs::Message::Ptr buildMessage(const cms::Message *m) const;
    
        MQS_DECLARE_LOGGER();
        boost::recursive_mutex _mtx;
    
        mqs::BrokerURI _broker;
        mqs::Destination _inQueue;
        mqs::Destination _outQueue;
        mqs::MessageSequenceGenerator::Ptr _msgSeqGen;

        shared_ptr<cms::Connection> _connection;
        shared_ptr<cms::Session> _session;
        shared_ptr<cms::MessageProducer> _producer;
        shared_ptr<cms::Destination> _producer_destination;

        struct Consumer {
            shared_ptr<mqs::Destination> mqs_destination;
            shared_ptr<cms::Destination> destination;
            shared_ptr<cms::MessageConsumer> consumer;
        };
        std::list<Consumer> _consumer;

        mqs::MessageListener* _messageListener;
        mqs::ExceptionListener* _exceptionListener;

        boost::mutex _incomingMessagesMutex;
        boost::condition_variable _incomingMessagesCondition;
        std::list<mqs::Message::Ptr> _incomingMessages;
    
        boost::mutex _awaitingResponseMtx;
        std::vector<mqs::Response*> _awaitingResponse;

        // internal state keeper
        bool _started;
        std::size_t _blocked_receivers;
        State _state;
    };
}

#endif // !MQS_CHANNEL_HPP

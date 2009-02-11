#ifndef MQS_MESSAGE_LISTENER_HPP
#define MQS_MESSAGE_LISTENER_HPP 1

#include <mqs/Message.hpp>

namespace mqs {
    class MessageListener {
    public:
        virtual void onMessage(const mqs::Message::Ptr &msg) = 0;
    };
}

#endif // ! MQS_MESSAGE_LISTENER_HPP

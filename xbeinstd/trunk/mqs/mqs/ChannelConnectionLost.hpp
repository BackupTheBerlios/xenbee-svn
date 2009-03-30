#ifndef MQS_CHANNEL_CONNECTION_LOST_HPP
#define MQS_CHANNEL_CONNECTION_LOST_HPP 1

#include <mqs/MQSException.hpp>

namespace mqs {
    class ChannelConnectionLost : public MQSException {
    public:
        ChannelConnectionLost() : MQSException("channel lost connection to server") {}
        virtual ~ChannelConnectionLost() throw() {}
    };
}

#endif

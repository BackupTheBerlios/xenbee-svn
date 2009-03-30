#ifndef MQS_CHANNEL_CONNECTION_FAILED_HPP
#define MQS_CHANNEL_CONNECTION_FAILED_HPP 1

#include <mqs/MQSException.hpp>

namespace mqs {
    class ChannelConnectionFailed : public MQSException {
    public:
        explicit
        ChannelConnectionFailed(const std::string &reason = "connection to server failed") : MQSException(reason) {}
        virtual ~ChannelConnectionFailed() throw() {}
    };
}

#endif

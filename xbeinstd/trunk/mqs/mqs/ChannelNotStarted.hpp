#ifndef MQS_CHANNEL_NOT_STARTED_HPP
#define MQS_CHANNEL_NOT_STARTED_HPP 1

#include <mqs/MQSException.hpp>

namespace mqs {
    class ChannelNotStarted : public MQSException {
    public:
        explicit
        ChannelNotStarted(const std::string &reason="channel not started") : MQSException(reason) {}
        virtual ~ChannelNotStarted() throw() {}
    };
}

#endif

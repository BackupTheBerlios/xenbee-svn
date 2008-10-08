#ifndef XBE_CHANNEL_CONNECT_HPP
#define XBE_CHANNEL_CONNECT_HPP 1

#include <xbe/ChannelCommandEvent.hpp>

namespace xbe {
    class ChannelConnect : public ChannelCommandEvent {
    public:
        ChannelConnect() {}
        ~ChannelConnect() {}

        virtual void execute(mqs::Channel::Ptr channel);
        virtual std::string str() const {
            return "channel.command.connect";
        }
    };
}

#endif // !XBE_CHANNEL_CONNECT_HPP

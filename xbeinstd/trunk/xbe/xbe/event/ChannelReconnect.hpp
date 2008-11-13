#ifndef XBE_CHANNEL_RECONNECT_HPP
#define XBE_CHANNEL_RECONNECT_HPP 1

#include <xbe/ChannelCommandEvent.hpp>

namespace xbe {
    namespace event {
        class ChannelReconnect : public ChannelCommandEvent {
            public:
                ChannelReconnect() {}
                ~ChannelReconnect() {}

                virtual void execute(mqs::Channel::Ptr channel);
                virtual std::string str() const {
                    return "channel.command.reconnect";
                }
        };
    }
}

#endif // !XBE_CHANNEL_RECONNECT_HPP

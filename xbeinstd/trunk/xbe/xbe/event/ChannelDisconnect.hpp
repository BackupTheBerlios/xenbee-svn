#ifndef XBE_CHANNEL_DISCONNECT_HPP
#define XBE_CHANNEL_DISCONNECT_HPP 1

#include <xbe/event/ChannelCommandEvent.hpp>

namespace xbe {
    namespace event {
        class ChannelDisconnect : public ChannelCommandEvent {
            public:
                ChannelDisconnect() {}
                ~ChannelDisconnect() {}

                virtual void execute(mqs::Channel::Ptr channel);
                virtual std::string str() const {
                    return "channel.command.disconnect";
                }
        };
    }
}

#endif // !XBE_CHANNEL_DISCONNNECT_HPP

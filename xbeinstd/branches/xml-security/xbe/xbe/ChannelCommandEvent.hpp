#ifndef XBE_CHANNEL_COMMAND_EVENT_HPP
#define XBE_CHANNEL_COMMAND_EVENT_HPP 1

#include <seda/SystemEvent.hpp>
#include <mqs/Channel.hpp>

namespace xbe {
    class ChannelCommandEvent : public seda::SystemEvent {
    public:
        virtual void execute(mqs::Channel::Ptr channel) = 0;
        virtual std::string str() const = 0;
    protected:
        ChannelCommandEvent() {}
        ~ChannelCommandEvent() {}
    };
}

#endif // !XBE_CHANNEL_COMMAND_EVENT_HPP

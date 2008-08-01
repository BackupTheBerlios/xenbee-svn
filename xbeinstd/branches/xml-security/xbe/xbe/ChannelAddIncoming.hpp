#ifndef XBE_CHANNEL_ADD_INCOMING_HPP
#define XBE_CHANNEL_ADD_INCOMING_HPP 1

#include <xbe/ChannelCommandEvent.hpp>
#include <mqs/Destination.hpp>

namespace xbe {
    class ChannelAddIncoming : public ChannelCommandEvent {
    public:
        ChannelAddIncoming(const mqs::Destination& queue)
        : _queue(queue) {}
        ~ChannelAddIncoming() {}

        virtual void execute(mqs::Channel::Ptr channel);
        virtual std::string str() const {
            return "channel.command.add-incoming";
        }
    private:
        mqs::Destination _queue;
    };
}

#endif // !XBE_CHANNEL_ADD_INCOMING_HPP

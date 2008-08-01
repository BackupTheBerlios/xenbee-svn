#ifndef XBE_CHANNEL_DEL_INCOMING_HPP
#define XBE_CHANNEL_DEL_INCOMING_HPP 1

#include <xbe/ChannelCommandEvent.hpp>
#include <mqs/Destination.hpp>

namespace xbe {
    class ChannelDelIncoming : public ChannelCommandEvent {
    public:
        ChannelDelIncoming(const mqs::Destination& queue)
        : _queue(queue) {}
        ~ChannelDelIncoming() {}

        virtual void execute(mqs::Channel::Ptr channel);
        virtual std::string str() const {
            return "channel.command.del-incoming";
        }
    private:
        mqs::Destination _queue;
    };
}

#endif // !XBE_CHANNEL_DEL_INCOMING_HPP

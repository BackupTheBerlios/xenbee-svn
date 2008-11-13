#ifndef XBE_CHANNEL_ADD_INCOMING_HPP
#define XBE_CHANNEL_ADD_INCOMING_HPP 1

#include <mqs/Channel.hpp>
#include <mqs/Destination.hpp>

#include <xbe/event/ChannelCommandEvent.hpp>

namespace xbe {
    namespace event {
        class ChannelAddIncoming : public xbe::event::ChannelCommandEvent {
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
}

#endif // !XBE_CHANNEL_ADD_INCOMING_HPP

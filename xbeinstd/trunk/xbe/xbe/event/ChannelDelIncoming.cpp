#include "ChannelDelIncoming.hpp"

using namespace xbe::event;

void
ChannelDelIncoming::execute(mqs::Channel::Ptr channel) {
    channel->delIncomingQueue(_queue);
}


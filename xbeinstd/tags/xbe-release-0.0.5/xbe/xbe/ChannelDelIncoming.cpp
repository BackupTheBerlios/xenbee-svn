#include "ChannelDelIncoming.hpp"

using namespace xbe;

void
ChannelDelIncoming::execute(mqs::Channel::Ptr channel) {
    channel->delIncomingQueue(_queue);
}


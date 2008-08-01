#include "ChannelAddIncoming.hpp"

using namespace xbe;

void
ChannelAddIncoming::execute(mqs::Channel::Ptr channel) {
    channel->addIncomingQueue(_queue);
}


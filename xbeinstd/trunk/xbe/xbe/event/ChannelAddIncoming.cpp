#include "ChannelAddIncoming.hpp"

using namespace xbe::event;

void
ChannelAddIncoming::execute(mqs::Channel::Ptr channel) {
    channel->addIncomingQueue(_queue);
}


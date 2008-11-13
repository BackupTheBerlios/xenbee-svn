#include "ChannelDisconnect.hpp"

using namespace xbe::event;

void
ChannelDisconnect::execute(mqs::Channel::Ptr channel) {
    channel->stop();
}


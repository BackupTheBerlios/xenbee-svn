#include "ChannelDisconnect.hpp"

using namespace xbe;

void
ChannelDisconnect::execute(mqs::Channel::Ptr channel) {
    channel->stop();
}


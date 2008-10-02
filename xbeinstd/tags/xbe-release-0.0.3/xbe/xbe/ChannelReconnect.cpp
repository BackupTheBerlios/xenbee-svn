#include "ChannelReconnect.hpp"

using namespace xbe;

void
ChannelReconnect::execute(mqs::Channel::Ptr channel) {
    channel->stop();
    channel->start();
}


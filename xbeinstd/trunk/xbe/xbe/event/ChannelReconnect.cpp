#include "ChannelReconnect.hpp"

using namespace xbe::event;

void
ChannelReconnect::execute(mqs::Channel::Ptr channel) {
    channel->stop();
    channel->start();
}


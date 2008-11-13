#include "ChannelConnect.hpp"

using namespace xbe::event;

void
ChannelConnect::execute(mqs::Channel::Ptr channel) {
    channel->start();
}

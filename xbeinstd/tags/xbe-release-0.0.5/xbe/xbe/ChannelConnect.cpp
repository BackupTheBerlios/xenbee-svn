#include "ChannelConnect.hpp"

using namespace xbe;

void
ChannelConnect::execute(mqs::Channel::Ptr channel) {
    channel->start();
}

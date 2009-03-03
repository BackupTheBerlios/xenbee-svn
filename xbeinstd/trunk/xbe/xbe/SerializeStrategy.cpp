#include "SerializeStrategy.hpp"

#include "xbemsg.pb.h"
#include "event/DecodedMessageEvent.hpp"
#include "event/EncodedMessageEvent.hpp"

using namespace xbe;
using namespace xbe::event;
using namespace xbe::messages;

SerializeStrategy::SerializeStrategy(const std::string &name,
                                         const std::string &next)
    : seda::ForwardStrategy(next), XBE_INIT_LOGGER(name) {}

void SerializeStrategy::perform(const seda::IEvent::Ptr &e) {
    if (DecodedMessageEvent *dme = dynamic_cast<DecodedMessageEvent*>(e.get())) {
        xbe::event::EncodedMessageEvent::Ptr eme(new xbe::event::EncodedMessageEvent(
                                                    dme->serialize(),
                                                    dme->destination(), dme->source()));
        XBE_LOG_DEBUG("serialized event: " << eme->str());
        ForwardStrategy::perform(eme);
    } else {
        XBE_LOG_WARN("received event that is not of type EncodedMessageEvent, dropping it.");
    }
}

#include "LifeSignEvent.hpp"
#include <xbe/xbemsg.pb.h>

#include <sstream>

using namespace xbe::event;
using namespace xbe::messages;

std::string LifeSignEvent::str() const {
    std::ostringstream oss;
    oss << "LifeSignEvent " 
                        << "(cid=" << conversation_id()
                        << " tstamp=" << tstamp()
                        << ")";
    return oss.str();
}

std::string LifeSignEvent::serialize() const {
    XbeMessage msg;
    Header *hdr = msg.mutable_header();
    hdr->set_conversation_id(conversation_id());
    
    LifeSign *payload = msg.mutable_life_sign();
    payload->set_tstamp(tstamp());

    XBE_LOG_DEBUG("created XbeMessage: " << msg.DebugString());
    std::string s;
    if (! msg.SerializeToString(&s)) {
        XBE_LOG_ERROR("failed to serialize to string!");
        throw std::runtime_error("failed to serialize to string!");
    } else {
        return s;
    }
}

LifeSignEvent::Ptr LifeSignEvent::deserialize(const std::string &s) {
    XbeMessage msg;
    if (! msg.ParseFromString(s)) {
        throw std::runtime_error("failed to de-serialize LifeSign from string!");
    }
    if (! msg.has_life_sign()) {
        throw std::runtime_error("XbeMessage did not contain an LifeSign element!");
    }
    LifeSignEvent::Ptr retval((new LifeSignEvent(msg.header().conversation_id()))->tstamp(msg.life_sign().tstamp()));

    return retval;
}

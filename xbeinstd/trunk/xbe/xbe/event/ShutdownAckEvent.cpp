#include "ShutdownAckEvent.hpp"
#include <xbe/xbemsg.pb.h>

#include <sstream>

using namespace xbe::event;
using namespace xbe::messages;

std::string ShutdownAckEvent::str() const {
    std::ostringstream oss;
    oss << "ShutdownAckEvent " 
                        << "(cid=" << conversation_id()
                        << ")";
    return oss.str();
}

std::string ShutdownAckEvent::serialize() const {
    XbeMessage msg;
    Header *hdr = msg.mutable_header();
    hdr->set_conversation_id(conversation_id());
    
    (void)msg.mutable_shutdown_ack();

    XBE_LOG_DEBUG("created XbeMessage: " << msg.DebugString());
    std::string s;
    if (! msg.SerializeToString(&s)) {
        XBE_LOG_ERROR("failed to serialize to string!");
        throw std::runtime_error("failed to serialize to string!");
    } else {
        return s;
    }
}

ShutdownAckEvent::Ptr ShutdownAckEvent::deserialize(const std::string &s) {
    XbeMessage msg;
    if (! msg.ParseFromString(s)) {
        throw std::runtime_error("failed to de-serialize ShutdownAck from string!");
    }
    if (! msg.has_shutdown_ack()) {
        throw std::runtime_error("XbeMessage did not contain an ShutdownAck element!");
    }
    ShutdownAckEvent::Ptr retval(new ShutdownAckEvent(msg.header().conversation_id()));

    return retval;
}

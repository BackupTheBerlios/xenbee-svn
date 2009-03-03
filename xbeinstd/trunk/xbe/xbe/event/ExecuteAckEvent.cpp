#include "ExecuteAckEvent.hpp"
#include <xbe/xbemsg.pb.h>

#include <sstream>

using namespace xbe::event;
using namespace xbe::messages;

std::string ExecuteAckEvent::str() const {
    std::ostringstream oss;
    oss << "ExecuteAckEvent " 
                        << "(cid=" << conversation_id()
                        << ")";
    return oss.str();
}

std::string ExecuteAckEvent::serialize() const {
    XbeMessage msg;
    Header *hdr = msg.mutable_header();
    hdr->set_conversation_id(conversation_id());
    
    (void) msg.mutable_execute_ack();
    XBE_LOG_DEBUG("created XbeMessage: " << msg.DebugString());

    std::string s;
    if (! msg.SerializeToString(&s)) {
        XBE_LOG_ERROR("failed to serialize to string!");
        throw std::runtime_error("failed to serialize to string!");
    } else {
        return s;
    }
}

ExecuteAckEvent::Ptr ExecuteAckEvent::deserialize(const std::string &s) {
    XbeMessage msg;
    if (! msg.ParseFromString(s)) {
        throw std::runtime_error("failed to de-serialize ExecuteAck from string!");
    }
    if (! msg.has_execute_ack()) {
        throw std::runtime_error("XbeMessage did not contain an ExecuteAck element!");
    }
    return ExecuteAckEvent::Ptr(new ExecuteAckEvent(msg.header().conversation_id()));
}

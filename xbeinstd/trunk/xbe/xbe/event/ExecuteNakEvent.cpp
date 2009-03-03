#include "ExecuteNakEvent.hpp"
#include <xbe/xbemsg.pb.h>

#include <sstream>

using namespace xbe::event;
using namespace xbe::messages;

std::string ExecuteNakEvent::str() const {
    std::ostringstream oss;
    oss << "ExecuteNakEvent " 
                        << "(cid=" << conversation_id()
                        << " reason=" << reason()
                        << " detail=" << detail()
                        << ")";
    return oss.str();
}

std::string ExecuteNakEvent::serialize() const {
    XbeMessage msg;
    Header *hdr = msg.mutable_header();
    hdr->set_conversation_id(conversation_id());
    
    ExecuteNak *payload=msg.mutable_execute_nak();
    payload->set_reason((xbe::messages::ExecuteNakReason)reason());
    if (detail().size()) payload->set_message(detail());
    XBE_LOG_DEBUG("created XbeMessage: " << msg.DebugString());

    std::string s;
    if (! msg.SerializeToString(&s)) {
        XBE_LOG_ERROR("failed to serialize to string!");
        throw std::runtime_error("failed to serialize to string!");
    } else {
        return s;
    }
}

ExecuteNakEvent::Ptr ExecuteNakEvent::deserialize(const std::string &s) {
    XbeMessage msg;
    if (! msg.ParseFromString(s)) {
        throw std::runtime_error("failed to de-serialize ExecuteNak from string!");
    }
    if (! msg.has_execute_nak()) {
        throw std::runtime_error("XbeMessage did not contain an ExecuteNak element!");
    }
    ExecuteNakEvent::Ptr retval(new ExecuteNakEvent(msg.header().conversation_id()));
    const ExecuteNak &nak(msg.execute_nak());
    retval->reason((ExecuteNakReason)nak.reason());
    if (nak.has_message())
        retval->detail(nak.message());
    return retval;
}

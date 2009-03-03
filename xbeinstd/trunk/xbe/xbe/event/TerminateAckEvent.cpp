#include "TerminateAckEvent.hpp"
#include <xbe/xbemsg.pb.h>

#include <sstream>

using namespace xbe::event;
using namespace xbe::messages;

std::string TerminateAckEvent::str() const {
    std::ostringstream oss;
    oss << "TerminateAckEvent " 
                        << "(cid=" << conversation_id()
                        << " task=" << task()
                        << ")";
    return oss.str();
}

std::string TerminateAckEvent::serialize() const {
    XbeMessage msg;
    Header *hdr = msg.mutable_header();
    hdr->set_conversation_id(conversation_id());
    
    TerminateAck *payload = msg.mutable_terminate_ack();
    payload->set_task(task());

    XBE_LOG_DEBUG("created XbeMessage: " << msg.DebugString());
    std::string s;
    if (! msg.SerializeToString(&s)) {
        XBE_LOG_ERROR("failed to serialize to string!");
        throw std::runtime_error("failed to serialize to string!");
    } else {
        return s;
    }
}

TerminateAckEvent::Ptr TerminateAckEvent::deserialize(const std::string &s) {
    XbeMessage msg;
    if (! msg.ParseFromString(s)) {
        throw std::runtime_error("failed to de-serialize TerminateAck from string!");
    }
    if (! msg.has_terminate_ack()) {
        throw std::runtime_error("XbeMessage did not contain an TerminateAck element!");
    }
    TerminateAckEvent::Ptr retval(new TerminateAckEvent(msg.header().conversation_id()));
    if (msg.terminate_ack().has_task()) {
        retval->task(msg.terminate_ack().task());
    }
    return retval;
}

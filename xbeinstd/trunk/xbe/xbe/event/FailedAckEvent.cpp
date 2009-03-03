#include "FailedAckEvent.hpp"
#include <xbe/xbemsg.pb.h>

#include <sstream>

using namespace xbe::event;
using namespace xbe::messages;

std::string FailedAckEvent::str() const {
    std::ostringstream oss;
    oss << "FailedAckEvent " 
                        << "(cid=" << conversation_id()
                        << " task=" << task()
                        << ")";
    return oss.str();
}

std::string FailedAckEvent::serialize() const {
    XbeMessage msg;
    Header *hdr = msg.mutable_header();
    hdr->set_conversation_id(conversation_id());
    
    FailedAck *payload = msg.mutable_failed_ack();
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

FailedAckEvent::Ptr FailedAckEvent::deserialize(const std::string &s) {
    XbeMessage msg;
    if (! msg.ParseFromString(s)) {
        throw std::runtime_error("failed to de-serialize FailedAck from string!");
    }
    if (! msg.has_failed_ack()) {
        throw std::runtime_error("XbeMessage did not contain an FailedAck element!");
    }
    FailedAckEvent::Ptr retval(new FailedAckEvent(msg.header().conversation_id()));
    if (msg.failed_ack().has_task()) {
        retval->task(msg.failed_ack().task());
    }

    return retval;
}

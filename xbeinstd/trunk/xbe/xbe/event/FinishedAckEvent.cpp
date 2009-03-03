#include "FinishedAckEvent.hpp"
#include <xbe/xbemsg.pb.h>

#include <sstream>

using namespace xbe::event;
using namespace xbe::messages;

std::string FinishedAckEvent::str() const {
    std::ostringstream oss;
    oss << "FinishedAckEvent " 
                        << "(cid=" << conversation_id()
                        << " tid=" << task_id()
                        << ")";
    return oss.str();
}

std::string FinishedAckEvent::serialize() const {
    XbeMessage msg;
    Header *hdr = msg.mutable_header();
    hdr->set_conversation_id(conversation_id());
    
    FinishedAck *payload = msg.mutable_finished_ack();
    if (task_id() >= 0) {
        payload->set_task(task_id());
    }

    XBE_LOG_DEBUG("created XbeMessage: " << msg.DebugString());
    std::string s;
    if (! msg.SerializeToString(&s)) {
        XBE_LOG_ERROR("failed to serialize to string!");
        throw std::runtime_error("failed to serialize to string!");
    } else {
        return s;
    }
}

FinishedAckEvent::Ptr FinishedAckEvent::deserialize(const std::string &s) {
    XbeMessage msg;
    if (! msg.ParseFromString(s)) {
        throw std::runtime_error("failed to de-serialize FinishedAck from string!");
    }
    if (! msg.has_finished_ack()) {
        throw std::runtime_error("XbeMessage did not contain an FinishedAck element!");
    }
    FinishedAckEvent::Ptr retval(new FinishedAckEvent(msg.header().conversation_id()));
    if (msg.finished_ack().has_task()) {
        retval->task_id(msg.finished_ack().task());
    }

    return retval;
}

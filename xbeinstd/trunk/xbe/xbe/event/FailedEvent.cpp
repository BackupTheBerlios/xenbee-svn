#include "FailedEvent.hpp"
#include <xbe/xbemsg.pb.h>

#include <sstream>

using namespace xbe::event;
using namespace xbe::messages;

std::string FailedEvent::str() const {
    std::ostringstream oss;
    oss << "FailedEvent " 
                        << "(cid=" << conversation_id()
                        << " task=" << task()
                        << " reason=" << reason()
                        << ")";
    return oss.str();
}

std::string FailedEvent::serialize() const {
    XbeMessage msg;
    Header *hdr = msg.mutable_header();
    hdr->set_conversation_id(conversation_id());
    
    Failed *payload = msg.mutable_failed();
    payload->set_reason((xbe::messages::FailReason)reason());
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

FailedEvent::Ptr FailedEvent::deserialize(const std::string &s) {
    XbeMessage msg;
    if (! msg.ParseFromString(s)) {
        throw std::runtime_error("failed to de-serialize Failed from string!");
    }
    if (! msg.has_failed()) {
        throw std::runtime_error("XbeMessage did not contain an Failed element!");
    }
    FailedEvent::Ptr retval(new FailedEvent(msg.header().conversation_id()));
    if (msg.failed().has_reason()) {
        retval->reason((FailReason)msg.failed().reason());
    }
    if (msg.failed().has_task()) {
        retval->task(msg.failed().task());
    }

    return retval;
}

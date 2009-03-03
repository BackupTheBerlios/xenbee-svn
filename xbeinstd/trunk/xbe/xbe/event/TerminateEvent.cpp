#include "TerminateEvent.hpp"
#include <xbe/xbemsg.pb.h>

#include <sstream>

using namespace xbe::event;
using namespace xbe::messages;

std::string TerminateEvent::str() const {
    std::ostringstream oss;
    oss << "TerminateEvent " 
                        << "(cid=" << conversation_id()
                        << ")";
    return oss.str();
}

std::string TerminateEvent::serialize() const {
    XbeMessage msg;
    Header *hdr = msg.mutable_header();
    hdr->set_conversation_id(conversation_id());
    
    Terminate *payload = msg.mutable_terminate();
    if (task() >= 0) payload->set_task(task());

    XBE_LOG_DEBUG("created XbeMessage: " << msg.DebugString());
    std::string s;
    if (! msg.SerializeToString(&s)) {
        XBE_LOG_ERROR("failed to serialize to string!");
        throw std::runtime_error("failed to serialize to string!");
    } else {
        return s;
    }
}

TerminateEvent::Ptr TerminateEvent::deserialize(const std::string &s) {
    XbeMessage msg;
    if (! msg.ParseFromString(s)) {
        throw std::runtime_error("failed to de-serialize Terminate from string!");
    }
    if (! msg.has_terminate()) {
        throw std::runtime_error("XbeMessage did not contain an Terminate element!");
    }
    TerminateEvent::Ptr retval((new TerminateEvent(msg.header().conversation_id())));
    if (msg.terminate().has_task()) {
        retval->task(msg.terminate().task());
    }
    return retval;
}

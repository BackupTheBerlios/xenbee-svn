#include "ShutdownEvent.hpp"
#include <xbe/xbemsg.pb.h>

#include <sstream>

using namespace xbe::event;
using namespace xbe::messages;

std::string ShutdownEvent::str() const {
    std::ostringstream oss;
    oss << "ShutdownEvent " 
                        << "(cid=" << conversation_id()
                        << ")";
    return oss.str();
}

std::string ShutdownEvent::serialize() const {
    XbeMessage msg;
    Header *hdr = msg.mutable_header();
    hdr->set_conversation_id(conversation_id());
    
    (void)msg.mutable_shutdown();

    XBE_LOG_DEBUG("created XbeMessage: " << msg.DebugString());
    std::string s;
    if (! msg.SerializeToString(&s)) {
        XBE_LOG_ERROR("failed to serialize to string!");
        throw std::runtime_error("failed to serialize to string!");
    } else {
        return s;
    }
}

ShutdownEvent::Ptr ShutdownEvent::deserialize(const std::string &s) {
    XbeMessage msg;
    if (! msg.ParseFromString(s)) {
        throw std::runtime_error("failed to de-serialize Shutdown from string!");
    }
    if (! msg.has_shutdown()) {
        throw std::runtime_error("XbeMessage did not contain an Shutdown element!");
    }
    ShutdownEvent::Ptr retval(new ShutdownEvent(msg.header().conversation_id()));

    return retval;
}

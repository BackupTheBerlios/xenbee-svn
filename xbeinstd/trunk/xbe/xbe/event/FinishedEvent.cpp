#include "FinishedEvent.hpp"
#include <xbe/xbemsg.pb.h>

#include <sstream>

using namespace xbe::event;
using namespace xbe::messages;

std::string FinishedEvent::str() const {
    std::ostringstream oss;
    oss << "FinishedEvent " 
                        << "(cid=" << conversation_id()
                        << " exitcode=" << exitcode()
                        << ")";
    return oss.str();
}

std::string FinishedEvent::serialize() const {
    XbeMessage msg;
    Header *hdr = msg.mutable_header();
    hdr->set_conversation_id(conversation_id());
    
    Finished *payload = msg.mutable_finished();
    payload->set_exitcode(exitcode());

    XBE_LOG_DEBUG("created XbeMessage: " << msg.DebugString());
    std::string s;
    if (! msg.SerializeToString(&s)) {
        XBE_LOG_ERROR("failed to serialize to string!");
        throw std::runtime_error("failed to serialize to string!");
    } else {
        return s;
    }
}

FinishedEvent::Ptr FinishedEvent::deserialize(const std::string &s) {
    XbeMessage msg;
    if (! msg.ParseFromString(s)) {
        throw std::runtime_error("failed to de-serialize Finished from string!");
    }
    if (! msg.has_finished()) {
        throw std::runtime_error("XbeMessage did not contain an Finished element!");
    }
    FinishedEvent::Ptr retval(new FinishedEvent(msg.header().conversation_id()));
    const xbe::messages::Finished& fin = msg.finished();
    retval->exitcode(fin.exitcode());

    return retval;
}

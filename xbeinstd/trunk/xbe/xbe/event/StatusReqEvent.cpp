#include "StatusReqEvent.hpp"
#include <xbe/xbemsg.pb.h>

#include <sstream>

using namespace xbe::event;
using namespace xbe::messages;

std::string StatusReqEvent::str() const {
    std::ostringstream oss;
    oss << "StatusReqEvent " 
                        << "(cid=" << conversation_id()
                        << " exec-status-task=" << execute_status_task()
                        << ")";
    return oss.str();
}

std::string StatusReqEvent::serialize() const {
    XbeMessage msg;
    Header *hdr = msg.mutable_header();
    hdr->set_conversation_id(conversation_id());
    
    StatusReq *payload = msg.mutable_status_req();
    payload->set_execute_status_task(execute_status_task());

    XBE_LOG_DEBUG("created XbeMessage: " << msg.DebugString());
    std::string s;
    if (! msg.SerializeToString(&s)) {
        XBE_LOG_ERROR("failed to serialize to string!");
        throw std::runtime_error("failed to serialize to string!");
    } else {
        return s;
    }
}

StatusReqEvent::Ptr StatusReqEvent::deserialize(const std::string &s) {
    XbeMessage msg;
    if (! msg.ParseFromString(s)) {
        throw std::runtime_error("failed to de-serialize StatusReq from string!");
    }
    if (! msg.has_status_req()) {
        throw std::runtime_error("XbeMessage did not contain an StatusReq element!");
    }
    StatusReqEvent::Ptr retval(new StatusReqEvent(msg.header().conversation_id()));
    const xbe::messages::StatusReq& req = msg.status_req();
    retval->execute_status_task(req.execute_status_task());

    return retval;
}

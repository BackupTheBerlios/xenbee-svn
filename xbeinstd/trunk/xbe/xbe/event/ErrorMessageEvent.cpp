#include "ErrorMessageEvent.hpp"
#include <xbe/xbemsg.pb.h>

#include <sstream>

using namespace xbe::event;
using namespace xbe::messages;

std::string ErrorMessageEvent::str() const {
    std::ostringstream oss;
    oss << "ErrorMessageEvent " 
                        << "(cid=" << conversation_id()
                        << ", code=" << error_code()
                        << ", msg=" << error_msg()
                        << ")";
    return oss.str();
}

std::string ErrorMessageEvent::serialize() const {
    XbeMessage msg;
    Header *hdr = msg.mutable_header();
    hdr->set_conversation_id(conversation_id());
    
    Error *payload = msg.mutable_error();
    payload->set_code((xbe::messages::ErrorCode)error_code());
    payload->set_message(error_msg());

    XBE_LOG_DEBUG("created XbeMessage: " << msg.DebugString());

    std::string s;
    if (! msg.SerializeToString(&s)) {
        XBE_LOG_ERROR("failed to serialize to string!");
        throw std::runtime_error("failed to serialize to string!");
    } else {
        return s;
    }
}

ErrorMessageEvent::Ptr ErrorMessageEvent::deserialize(const std::string &s) {
    XbeMessage msg;
    if (! msg.ParseFromString(s)) {
        throw std::runtime_error("failed to de-serialize ErrorMessage from string!");
    }
    if (! msg.has_error()) {
        throw std::runtime_error("XbeMessage did not contain an Error element!");
    }
    ErrorMessageEvent::Ptr retval(new ErrorMessageEvent(msg.header().conversation_id()));
    retval->error_code(msg.error().code());
    retval->error_msg(msg.error().message());
    return retval;
}

#include "StatusEvent.hpp"
#include <xbe/xbemsg.pb.h>

#include <sstream>

using namespace xbe::event;
using namespace xbe::messages;

std::string StatusEvent::str() const {
    std::ostringstream oss;
    oss << "StatusEvent " 
                        << "(cid=" << conversation_id()
                        << " state=" << state()
                        << " status-code=" << taskStatusCode()
                        << ")";
    return oss.str();
}

std::string StatusEvent::serialize() const {
    XbeMessage msg;
    Header *hdr = msg.mutable_header();
    hdr->set_conversation_id(conversation_id());
    
    Status *payload = msg.mutable_status();
    payload->set_status((::xbe::messages::StatusCode)state());
    if (taskStatusCode() >= 0) {
        payload->set_status_task_exit_code(taskStatusCode());
    }
    if (taskStatusStdOut().size()) {
        payload->set_stdout(taskStatusStdOut());
    }
    if (taskStatusStdErr().size()) {
        payload->set_stderr(taskStatusStdErr());
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

StatusEvent::Ptr StatusEvent::deserialize(const std::string &s) {
    XbeMessage msg;
    if (! msg.ParseFromString(s)) {
        throw std::runtime_error("failed to de-serialize Status from string!");
    }
    if (! msg.has_status()) {
        throw std::runtime_error("XbeMessage did not contain an Status element!");
    }
    StatusEvent::Ptr retval(new StatusEvent(msg.header().conversation_id()));
    const xbe::messages::Status& status = msg.status();
    retval->state((xbe::event::StatusEvent::StatusCode)status.status());
    if (status.has_status_task_exit_code()) retval->taskStatusCode(status.status_task_exit_code());
    if (status.has_stdout()) retval->taskStatusStdOut(status.stdout());
    if (status.has_stderr()) retval->taskStatusStdErr(status.stderr());

    return retval;
}

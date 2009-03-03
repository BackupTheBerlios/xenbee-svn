#include "ExecuteEvent.hpp"
#include <xbe/xbemsg.pb.h>

#include <sstream>

using namespace xbe::event;
using namespace xbe::messages;

std::string ExecuteEvent::str() const {
    std::ostringstream oss;
    oss << "ExecuteEvent " 
                        << "(cid=" << conversation_id()
                        << ")";
    return oss.str();
}

std::string ExecuteEvent::serialize() const {
    XbeMessage msg;
    Header *hdr = msg.mutable_header();
    hdr->set_conversation_id(conversation_id());
    
    Execute *payload = msg.mutable_execute();
    if (taskData().is_valid()) {
        const TaskData &td = taskData();
        Task *task = payload->mutable_main_task();

        task->set_executable(td.path());
        for (TaskData::params_t::const_iterator it(td.params().begin() + 1);
             it !=  td.params().end();
             it++) {
            task->add_argument(*it);
        }
        for (TaskData::env_t::const_iterator it(td.env().begin());
             it != td.env().end();
             it++) {
            Task_Env *envptr(task->add_env());
            envptr->set_key(it->first);
            envptr->set_val(it->second);
        }
        task->set_stdin(td.stdIn());
        task->set_stdout(td.stdOut());
        task->set_stderr(td.stdErr());
        task->set_wd(td.wd().string());
    }
    if (statusTaskData().is_valid()) {
        const TaskData &td = statusTaskData();
        Task *task = payload->mutable_status_task();

        task->set_executable(td.path());
        for (TaskData::params_t::const_iterator it(td.params().begin() + 1);
             it !=  td.params().end();
             it++) {
            task->add_argument(*it);
        }
        for (TaskData::env_t::const_iterator it(td.env().begin());
             it != td.env().end();
             it++) {
            Task_Env *envptr(task->add_env());
            envptr->set_key(it->first);
            envptr->set_val(it->second);
        }
        task->set_stdin(td.stdIn());
        task->set_stdout(td.stdOut());
        task->set_stderr(td.stdErr());
        task->set_wd(td.wd().string());
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

ExecuteEvent::Ptr ExecuteEvent::deserialize(const std::string &s) {
    XbeMessage msg;
    if (! msg.ParseFromString(s)) {
        throw std::runtime_error("failed to de-serialize Execute from string!");
    }
    if (! msg.has_execute()) {
        throw std::runtime_error("XbeMessage did not contain an Execute element!");
    }
    ExecuteEvent::Ptr retval(new ExecuteEvent(msg.header().conversation_id()));
    if (msg.execute().has_main_task()) {
        const Task &task = msg.execute().main_task();
        TaskData td(task.executable());
        for (int i = 0; i < task.argument_size(); i++) {
            td.params().push_back(task.argument(i));
        }
        for (int i = 0; i < task.env_size(); i++) {
            td.env()[task.env(i).key()] = task.env(i).val();
        }
        if (task.has_stdin()) td.stdIn(task.stdin());
        if (task.has_stdout()) td.stdOut(task.stdout());
        if (task.has_stderr()) td.stdErr(task.stderr());
        if (task.has_wd()) td.wd(boost::filesystem::path(task.wd()));

       retval->taskData(td);
    }
    if (msg.execute().has_status_task()) {
        const Task &task = msg.execute().status_task();
        TaskData td(task.executable());
        for (int i = 0; i < task.argument_size(); i++) {
            td.params().push_back(task.argument(i));
        }
        for (int i = 0; i < task.env_size(); i++) {
            td.env()[task.env(i).key()] = task.env(i).val();
        }
        if (task.has_stdin()) td.stdIn(task.stdin());
        if (task.has_stdout()) td.stdOut(task.stdout());
        if (task.has_stderr()) td.stdErr(task.stderr());
        if (task.has_wd()) td.wd(boost::filesystem::path(task.wd()));

        retval->taskData(td);
    }

    return retval;
}

#ifndef XBE_EXECUTE_EVENT_HPP
#define XBE_EXECUTE_EVENT_HPP 1

#include <xbe/event/XbeInstdEvent.hpp>
#include <xbe/TaskData.hpp>
#include <boost/filesystem.hpp>

#include <string>
#include <list>
#include <map>

namespace xbe {
    namespace event {
        class ExecuteEvent : public xbe::event::XbeInstdEvent {
            public:
                ExecuteEvent(const std::string &to, const std::string &from, const std::string &conversationID)
                : xbe::event::XbeInstdEvent(to, from, conversationID) {}
                virtual ~ExecuteEvent() {}

                virtual std::string str() const {return "execute";}

                void taskData(const TaskData & td) { _taskData = td; }
                TaskData & taskData() { return _taskData; }
                const TaskData & taskData() const { return _taskData; }

                void statusTaskData(const TaskData &sd) { _statusTaskData = sd; }
                TaskData & statusTaskData() { return _statusTaskData; }
                const TaskData & statusTaskData() const { return _statusTaskData; }
            private:
                TaskData _taskData;
                TaskData _statusTaskData;
        };
    }
}

#endif // !XBE_EXECUTE_EVENT_HPP

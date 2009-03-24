#ifndef XBE_EXECUTE_EVENT_HPP
#define XBE_EXECUTE_EVENT_HPP 1

#include <xbe/common/common.hpp>
#include <xbe/event/DecodedMessageEvent.hpp>
#include <xbe/TaskData.hpp>
#include <boost/filesystem.hpp>

#include <string>
#include <list>
#include <map>

namespace xbe {
    namespace event {
        class ExecuteEvent : public xbe::event::DecodedMessageEvent {
            public:
                typedef std::tr1::shared_ptr<ExecuteEvent> Ptr;

                ExecuteEvent(const std::string &conversation_id, const mqs::Destination &dst="", const mqs::Destination &src="")
                : xbe::event::DecodedMessageEvent(conversation_id, "ExecuteEvent", dst, src), XBE_INIT_LOGGER("ExecuteEvent") {}
                virtual ~ExecuteEvent() {}

                virtual std::string str() const;

                void taskData(const TaskData & td) { _taskData = td; }
                TaskData & taskData() { return _taskData; }
                const TaskData & taskData() const { return _taskData; }

                void statusTaskData(const TaskData &sd) { _statusTaskData = sd; }
                TaskData & statusTaskData() { return _statusTaskData; }
                const TaskData & statusTaskData() const { return _statusTaskData; }

                virtual std::string serialize() const;
                static Ptr deserialize(const std::string &);
            private:
                XBE_DECLARE_LOGGER();
                TaskData _taskData;
                TaskData _statusTaskData;
        };
    }
}

#endif // !XBE_EXECUTE_EVENT_HPP

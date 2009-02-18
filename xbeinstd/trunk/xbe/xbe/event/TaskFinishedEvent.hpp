#ifndef XBE_TASK_FINISHED_EVENT_HPP
#define XBE_TASK_FINISHED_EVENT_HPP 1

#include <seda/UserEvent.hpp>

namespace xbe {
    namespace event {
        class TaskFinishedEvent : public seda::UserEvent {
            public:
                explicit
                TaskFinishedEvent(int exitcode) : exitcode_(exitcode) {}
                virtual ~TaskFinishedEvent() {}

                virtual std::string str() const {return "task-finished";}
                int exitcode() const { return exitcode_; }
            private:
                int exitcode_;
        };
    }
}

#endif // !XBE_TASK_FINISHED_EVENT_HPP

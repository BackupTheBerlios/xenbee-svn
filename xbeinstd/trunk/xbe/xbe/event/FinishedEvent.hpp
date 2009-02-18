#ifndef XBE_FINISHED_EVENT_HPP
#define XBE_FINISHED_EVENT_HPP 1

#include <xbe/event/XbeInstdEvent.hpp>

namespace xbe {
    namespace event {
        class FinishedEvent : public xbe::event::XbeInstdEvent {
            public:
                FinishedEvent(const std::string &to, const std::string &from, const std::string &conversationID, int exitcode)
                : xbe::event::XbeInstdEvent(to, from, conversationID, 0), exitcode_(exitcode) {}
                virtual ~FinishedEvent() {}

                virtual std::string str() const {return "finished";}

                int exitcode() const { return exitcode_; }
            private:
                int exitcode_;
        };
    }
}

#endif // !XBE_FINISHED_EVENT_HPP

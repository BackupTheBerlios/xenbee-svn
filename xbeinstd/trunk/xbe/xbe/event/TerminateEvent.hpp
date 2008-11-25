#ifndef XBE_TERMINATE_EVENT_HPP
#define XBE_TERMINATE_EVENT_HPP 1

#include <xbe/event/XbeInstdEvent.hpp>

namespace xbe {
    namespace event {
        class TerminateEvent : public xbe::event::XbeInstdEvent {
            public:
                TerminateEvent(const std::string &to, const std::string &from, const std::string &conversationID)
                : xbe::event::XbeInstdEvent(to, from, conversationID) {}
                virtual ~TerminateEvent() {}

                virtual std::string str() const {return "terminate";}
        };
    }
}

#endif // !XBE_TERMINATE_EVENT_HPP

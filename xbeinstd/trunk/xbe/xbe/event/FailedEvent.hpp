#ifndef XBE_FAILED_EVENT_HPP
#define XBE_FAILED_EVENT_HPP 1

#include <xbe/event/XbeInstdEvent.hpp>

namespace xbe {
    namespace event {
        class FailedEvent : public xbe::event::XbeInstdEvent {
            public:
                FailedEvent(const std::string &to, const std::string &from, const std::string &conversationID)
                : xbe::event::XbeInstdEvent(to, from, conversationID) {}
                virtual ~FailedEvent() {}

                virtual std::string str() const {return "dummy";}
        };
    }
}

#endif // !XBE_FAILED_EVENT_HPP

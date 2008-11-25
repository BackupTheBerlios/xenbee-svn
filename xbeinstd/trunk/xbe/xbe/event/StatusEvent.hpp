#ifndef XBE_status_EVENT_HPP
#define XBE_status_EVENT_HPP 1

#include <xbe/event/XbeInstdEvent.hpp>

namespace xbe {
    namespace event {
        class StatusEvent : public xbe::event::XbeInstdEvent {
            public:
                StatusEvent(const std::string &to, const std::string &from, const std::string &conversationID)
                : xbe::event::XbeInstdEvent(to, from, conversationID) {}
                virtual ~StatusEvent() {}

                virtual std::string str() const {return "status";}
        };
    }
}

#endif // !XBE_status_EVENT_HPP

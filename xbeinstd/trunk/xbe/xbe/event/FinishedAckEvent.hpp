#ifndef XBE_FINISHED_ACK_EVENT_HPP
#define XBE_FINISHED_ACK_EVENT_HPP 1

#include <xbe/event/XbeInstdEvent.hpp>

namespace xbe {
    namespace event {
        class FinishedAckEvent : public xbe::event::XbeInstdEvent {
            public:
                FinishedAckEvent(const std::string &to, const std::string &from, const std::string &conversationID)
                : XbeInstdEvent(to, from, conversationID) {}
                virtual ~FinishedAckEvent() {}

                virtual std::string str() const {return "dummy";}
        };
    }
}

#endif // !XBE_FINISHED_ACK_EVENT_HPP

#ifndef XBE_EXECUTE_ACK_EVENT_HPP
#define XBE_EXECUTE_ACK_EVENT_HPP 1

#include <xbe/event/XbeInstdEvent.hpp>

namespace xbe {
    namespace event {
        class ExecuteAckEvent : public xbe::event::XbeInstdEvent {
            public:
                ExecuteAckEvent(const std::string &to, const std::string &from, const std::string &conversationID)
                : xbe::event::XbeInstdEvent(to, from, conversationID) {}
                virtual ~ExecuteAckEvent() {}

                virtual std::string str() const {return "execute-ack";}
        };
    }
}

#endif // !XBE_EXECUTE_ACK_EVENT_HPP

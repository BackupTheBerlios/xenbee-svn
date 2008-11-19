#ifndef XBE_shutdownack_EVENT_HPP
#define XBE_shutdownack_EVENT_HPP 1

#include <xbe/event/XbeInstdEvent.hpp>

namespace xbe {
    namespace event {
        class ShutdownAckEvent : public xbe::event::XbeInstdEvent {
            public:
                ShutdownAckEvent(const std::string &to, const std::string &from, const std::string &conversationID)
                : XbeInstdEvent(to, from, conversationID) {}
                virtual ~ShutdownAckEvent() {}

                virtual std::string str() const {return "dummy";}
        };
    }
}

#endif // !XBE_shutdownack_EVENT_HPP

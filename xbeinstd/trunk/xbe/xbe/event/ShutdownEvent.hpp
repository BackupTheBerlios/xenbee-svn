#ifndef XBE_shutdown_EVENT_HPP
#define XBE_shutdown_EVENT_HPP 1

#include <xbe/event/XbeInstdEvent.hpp>

namespace xbe {
    namespace event {
        class ShutdownEvent : public xbe::event::XbeInstdEvent {
            public:
                ShutdownEvent(const std::string &to, const std::string &from, const std::string &conversationID)
                : XbeInstdEvent(to, from, conversationID) {}
                virtual ~ShutdownEvent() {}

                virtual std::string str() const {return "shutdown";}
        };
    }
}

#endif // !XBE_shutdown_EVENT_HPP

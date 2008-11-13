#ifndef XBE_TERMINATE_ACK_EVENT_HPP
#define XBE_TERMINATE_ACK_EVENT_HPP 1

#include <xbe/event/XbeInstdEvent.hpp>

namespace xbe {
    namespace event {
        class TerminateAckEvent : public xbe::event::XbeInstdEvent {
            public:
                TerminateAckEvent() {}
                virtual ~TerminateAckEvent() {}

                virtual std::string str() const {return "dummy";}
        };
    }
}

#endif // !XBE_TERMINATE_ACK_EVENT_HPP

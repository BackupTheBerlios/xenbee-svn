#ifndef XBE_FAILED_ACK_EVENT_HPP
#define XBE_FAILED_ACK_EVENT_HPP 1

#include <xbe/event/XbeInstdEvent.hpp>

namespace xbe {
    namespace event {
        class FailedAckEvent : public xbe::event::XbeInstdEvent {
            public:
                FailedAckEvent() {}
                virtual ~FailedAckEvent() {}

                virtual std::string str() const {return "dummy";}
        };
    }
}

#endif // !XBE_FAILED_ACK_EVENT_HPP

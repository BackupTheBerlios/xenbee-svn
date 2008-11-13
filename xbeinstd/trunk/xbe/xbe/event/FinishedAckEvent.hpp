#ifndef XBE_FINISHED_ACK_EVENT_HPP
#define XBE_FINISHED_ACK_EVENT_HPP 1

#include <xbe/event/XbeInstdEvent.hpp>

namespace xbe {
    namespace event {
        class FinishedAckEvent : public xbe::event::XbeInstdEvent {
            public:
                FinishedAckEvent() {}
                virtual ~FinishedAckEvent() {}

                virtual std::string str() const {return "dummy";}
        };
    }
}

#endif // !XBE_FINISHED_ACK_EVENT_HPP

#ifndef XBE_EXECUTE_ACK_EVENT_HPP
#define XBE_EXECUTE_ACK_EVENT_HPP 1

#include <xbe/event/XbeInstdEvent.hpp>

namespace xbe {
    namespace event {
        class ExecuteAckEvent : public xbe::event::XbeInstdEvent {
            public:
                ExecuteAckEvent() {}
                virtual ~ExecuteAckEvent() {}

                virtual std::string str() const {return "dummy";}
        };
    }
}

#endif // !XBE_EXECUTE_ACK_EVENT_HPP

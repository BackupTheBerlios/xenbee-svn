#ifndef XBE_TERMINATE_EVENT_HPP
#define XBE_TERMINATE_EVENT_HPP 1

#include <xbe/event/XbeInstdEvent.hpp>

namespace xbe {
    namespace event {
        class TerminateEvent : public xbe::event::XbeInstdEvent {
            public:
                TerminateEvent() {}
                virtual ~TerminateEvent() {}

                virtual std::string str() const {return "dummy";}
        };
    }
}

#endif // !XBE_TERMINATE_EVENT_HPP

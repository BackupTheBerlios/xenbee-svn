#ifndef XBE_status_EVENT_HPP
#define XBE_status_EVENT_HPP 1

#include <xbe/event/XbeInstdEvent.hpp>

namespace xbe {
    namespace event {
        class StatusEvent : public xbe::event::XbeInstdEvent {
            public:
                StatusEvent() {}
                virtual ~StatusEvent() {}

                virtual std::string str() const {return "dummy";}
        };
    }
}

#endif // !XBE_status_EVENT_HPP

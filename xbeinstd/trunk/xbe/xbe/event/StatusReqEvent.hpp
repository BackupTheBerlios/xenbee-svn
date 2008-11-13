#ifndef XBE_STATUS_REQ_EVENT_HPP
#define XBE_STATUS_REQ_EVENT_HPP 1

#include <xbe/event/XbeInstdEvent.hpp>

namespace xbe {
    namespace event {
        class StatusReqEvent : public xbe::event::XbeInstdEvent {
            public:
                StatusReqEvent() {}
                virtual ~StatusReqEvent() {}

                virtual std::string str() const {return "dummy";}
        };
    }
}

#endif // !XBE_STATUS_REQ_EVENT_HPP

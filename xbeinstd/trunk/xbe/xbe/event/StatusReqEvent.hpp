#ifndef XBE_STATUS_REQ_EVENT_HPP
#define XBE_STATUS_REQ_EVENT_HPP 1

#include <seda/UserEvent.hpp>

namespace xbe {
    namespace event {
        class StatusReqEvent : public seda::UserEvent {
            public:
                StatusReqEvent() {}
                virtual ~StatusReqEvent() {}

                virtual std::string str() const {return "dummy";}
        };
    }
}

#endif // !XBE_STATUS_REQ_EVENT_HPP

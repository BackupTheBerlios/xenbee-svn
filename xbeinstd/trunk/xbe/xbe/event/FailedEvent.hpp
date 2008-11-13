#ifndef XBE_FAILED_EVENT_HPP
#define XBE_FAILED_EVENT_HPP 1

#include <seda/UserEvent.hpp>

namespace xbe {
    namespace event {
        class FailedEvent : public seda::UserEvent {
            public:
                FailedEvent() {}
                virtual ~FailedEvent() {}

                virtual std::string str() const {return "dummy";}
        };
    }
}

#endif // !XBE_FAILED_EVENT_HPP

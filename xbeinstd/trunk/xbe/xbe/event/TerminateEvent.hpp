#ifndef XBE_TERMINATE_EVENT_HPP
#define XBE_TERMINATE_EVENT_HPP 1

#include <seda/UserEvent.hpp>

namespace xbe {
    namespace event {
        class TerminateEvent : public seda::UserEvent {
            public:
                TerminateEvent() {}
                virtual ~TerminateEvent() {}

                virtual std::string str() const {return "dummy";}
        };
    }
}

#endif // !XBE_TERMINATE_EVENT_HPP

#ifndef XBE_XBEINSTD_EVENT_HPP
#define XBE_XBEINSTD_EVENT_HPP 1

#include <seda/UserEvent.hpp>

namespace xbe {
    namespace event {
        class XbeInstdEvent : public seda::UserEvent {
            public:
                XbeInstdEvent() {}
                virtual ~XbeInstdEvent() {}

                virtual std::string str() const = 0;

                virtual std::string & conversationID() const = 0;
                virtual std::string & from() const = 0;
                virtual std::string & to() const = 0;
        };
    }
}

#endif // !XBE_XBEINSTD_EVENT_HPP

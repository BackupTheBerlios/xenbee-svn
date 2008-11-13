#ifndef XBE_shutdown_EVENT_HPP
#define XBE_shutdown_EVENT_HPP 1

#include <xbe/event/XbeInstdEvent.hpp>

namespace xbe {
    namespace event {
        class ShutdownEvent : public xbe::event::XbeInstdEvent {
            public:
                ShutdownEvent() {}
                virtual ~ShutdownEvent() {}

                virtual std::string str() const {return "dummy";}
        };
    }
}

#endif // !XBE_shutdown_EVENT_HPP

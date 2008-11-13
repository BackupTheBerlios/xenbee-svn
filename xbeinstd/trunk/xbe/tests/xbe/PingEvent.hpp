#ifndef TESTS_XBE_PING_EVENT_HPP
#define TESTS_XBE_PING_EVENT_HPP 1

#include <xbe/event/XMLMessageEvent.hpp>

namespace tests {
    namespace xbe {
        class PingEvent : public ::xbe::event::XMLMessageEvent {
        public:
            PingEvent(const xbemsg::message_t& m) :
                ::xbe::event::XMLMessageEvent(m) {}
            virtual ~PingEvent() {}
        };
    }
}

#endif // !TESTS_XBE_PING_EVENT_HPP

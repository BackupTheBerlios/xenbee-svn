#ifndef TESTS_XBE_PING_EVENT_HPP
#define TESTS_XBE_PING_EVENT_HPP 1

#include <xbe/XMLMessageEvent.hpp>

namespace tests {
    namespace xbe {
        class PingEvent : public ::xbe::XMLMessageEvent {
        public:
            PingEvent(const xbemsg::message_t& m) :
                ::xbe::XMLMessageEvent(m) {}
            virtual ~PingEvent() {}
        };
    }
}

#endif // !TESTS_XBE_PING_EVENT_HPP

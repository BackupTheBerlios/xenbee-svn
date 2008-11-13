#ifndef TESTS_XBE_PONG_EVENT_HPP
#define TESTS_XBE_PONG_EVENT_HPP 1

#include <xbe/event/XMLMessageEvent.hpp>

namespace tests {
    namespace xbe {
        class PongEvent : public ::xbe::event::XMLMessageEvent {
        public:
            PongEvent(const xbemsg::message_t& m) :
                ::xbe::event::XMLMessageEvent(m) {}
            virtual ~PongEvent() {}
        };
    }
}

#endif // !TESTS_XBE_PING_EVENT_HPP

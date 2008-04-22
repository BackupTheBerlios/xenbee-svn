#ifndef TESTS_XBE_PING_PONG_HPP
#define TESTS_XBE_PING_PONG_HPP 1

#include <tests/xbe/PingEvent.hpp>
#include <tests/xbe/PongEvent.hpp>

#include <tests/xbe/PingPong_sm.h>

namespace tests {
    namespace xbe {
        class PingPong {
        public:
            PingPong();
            ~PingPong();

        public: // StateMachine callbacks
            void start();
            void sendPing(const tests::xbe::PongEvent&);
            void sendPong(const tests::xbe::PingEvent&);
            void stop();
        };
    }
}


#endif // ! TESTS_XBE_PING_PONG_HPP

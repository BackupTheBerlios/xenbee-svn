#ifndef TESTS_XBE_PING_PONG_HPP
#define TESTS_XBE_PING_PONG_HPP 1

#include <seda/Stage.hpp>
#include <seda/Strategy.hpp>
#include <xbe/XMLMessageDispatcher.hpp>

#include <tests/xbe/PingEvent.hpp>
#include <tests/xbe/PongEvent.hpp>

#include <tests/xbe/PingPong_sm.h>

namespace tests {
    namespace xbe {
        class PingPong : ::xbe::XMLMessageDispatcher {
        public:
            PingPong(const seda::Strategy::Ptr& s, const seda::Stage::Ptr& out, bool initialSend=false);
            ~PingPong();

        public: // StateMachine callbacks
            void start();
            void sendPing(const tests::xbe::PongEvent&);
            void sendPong(const tests::xbe::PingEvent&);
            void stop();

        protected: // message dispatcher
            virtual void dispatch(const xbemsg::message_t& msg);
            
        protected:
            PingPongContext _fsm;  // what to do with incoming events
            seda::Stage::Ptr _out; // where to send generated events

        private:
            bool _initialSend; // perform an inital send operation during start up
        };
    }
}

#endif // ! TESTS_XBE_PING_PONG_HPP

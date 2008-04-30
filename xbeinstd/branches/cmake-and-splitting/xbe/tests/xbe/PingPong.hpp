#ifndef TESTS_XBE_PING_PONG_HPP
#define TESTS_XBE_PING_PONG_HPP 1

#include <string>

#include <seda/ForwardStrategy.hpp>

#include <tests/xbe/PingEvent.hpp>
#include <tests/xbe/PongEvent.hpp>

#include <tests/xbe/PingPong_sm.h>

namespace tests {
    namespace xbe {
        class PingPong : public ::seda::ForwardStrategy {
        public:
            typedef std::tr1::shared_ptr<PingPong> Ptr;
            
            PingPong(const std::string& name,
                     const std::string& next,
                     const std::string& to,
                     const std::string& from,
                     std::size_t maxMessages,
                     bool initialSend=false);
            ~PingPong();

        public:
            void perform(const seda::IEvent::Ptr& e) const;

            void doStart();
            void doStop();
            
        public: // StateMachine callbacks
            void start();
            void sendPing(const tests::xbe::PongEvent&);
            void sendPong(const tests::xbe::PingEvent&);
            void stop();

            std::size_t maxMessages() const { return _maxMessages; }
            std::size_t sentMessages() const { return _sentMessages; }
        protected: // message dispatcher
            virtual void dispatch(const xbemsg::message_t& msg);
            
        protected:
            PingPongContext _fsm;  // what to do with incoming events

        private:
            void incSentMessages() { _sentMessages++; }

            std::string _to;
            std::string _from;
            std::size_t _maxMessages;
            std::size_t _sentMessages;
            bool _initialSend; // perform an inital send operation during start up
        };
    }
}

#endif // ! TESTS_XBE_PING_PONG_HPP

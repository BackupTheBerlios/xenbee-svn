#include <xbe/ChannelEventQueueAdapter.hpp>
#include <mqs/Channel.hpp>

#include "PingPong.hpp"

using namespace tests::xbe;

PingPong::PingPong(const seda::Strategy::Ptr& s, const seda::Stage::Ptr& out, bool initialSend)
    : ::xbe::XMLMessageDispatcher(s), _fsm(*this), _out(out), _initialSend(initialSend)
{ }

PingPong::~PingPong() {}

void PingPong::start() {
    if (_initialSend) {
        // generate a new PingEvent and send it to 'out'
    }
}

void PingPong::dispatch(const xbemsg::message_t& msg) {
    // analyse type of message
    // if (typeof(msg) == PongEvent)
    //    _fsm.Ping(msg)
    // else if (typeof(msg) == PingEvent)
    //    _fsm.Pong(msg)
    // else
    //    log erroneous message arrival
}

void PingPong::stop() {
    
}

void PingPong::sendPong(const tests::xbe::PingEvent& m) {
    // PongEvent pong(...);
    // _out->send(pong);
}

void PingPong::sendPing(const tests::xbe::PongEvent& m) {
    // PingEvent ping(...);
    // _out->send(ping);
}

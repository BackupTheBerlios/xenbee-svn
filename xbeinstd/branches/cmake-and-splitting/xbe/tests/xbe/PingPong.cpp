#include <seda/StageRegistry.hpp>
#include <seda/Stage.hpp>

#include <xbe/ChannelEventQueueAdapter.hpp>
#include <mqs/Channel.hpp>
#include <xbe/xbe-msg.hpp>
#include <xsd/cxx/xml/string.hxx>
#include <xbe/XMLMessageEvent.hpp>

#include "PingPong.hpp"

using namespace tests::xbe;
namespace xml = xsd::cxx::xml;

PingPong::PingPong(const std::string& name,
                   const std::string& next,
                   const std::string& to,
                   const std::string& from,
                   std::size_t maxMessages,
                   bool initialSend) :
    ::seda::ForwardStrategy(name, next),
    _fsm(*this),
    _to(to),
    _from(from),
    _maxMessages(maxMessages),
    _sentMessages(0),
    _initialSend(initialSend)
{ }

PingPong::~PingPong() {}



void PingPong::perform(const seda::IEvent::Ptr& e) const {
    if (const ::xbe::XMLMessageEvent* xmlEvent = dynamic_cast<const ::xbe::XMLMessageEvent*>(e.get())) {
        const_cast<PingPong*>(this)->dispatch(xmlEvent->message());
    }
}

void PingPong::dispatch(const xbemsg::message_t& msg) {
    // analyse type of message
    if (msg.body().any().size()) {
        if (xml::transcode<char>(msg.body().any().front().getLocalName()) == "Ping") {
            ::tests::xbe::PingEvent pe(msg);
            _fsm.Ping(pe);
        } else if (xml::transcode<char>(msg.body().any().front().getLocalName()) == "Pong") {
            ::tests::xbe::PongEvent pe(msg);
            _fsm.Pong(pe);
        } else {
            LOG_WARN("got a message with illegal content!");
        }
    } else {
        LOG_WARN("got a message without any content!");
    }
}

void PingPong::doStart() {
    _fsm.Start();
}

void PingPong::doStop() {
    _fsm.Stop();
}

void PingPong::stop() {
    
}

void PingPong::start() {
    if (_initialSend) {
        LOG_DEBUG("sending ping " << (_sentMessages+1));

        // generate a new PingEvent and send it to 'out'
        xbemsg::header_t hdr(_to, _from);
        xbemsg::body_t body;

        body.any().push_back(body.dom_document().createElementNS(xml::string("http://www.xenbee.net/schema/2008/02/pingpong").c_str(),
                                                                 xml::string("Ping").c_str()));
        xbemsg::message_t msg(hdr, body);

        seda::ForwardStrategy::perform(seda::IEvent::Ptr(new ::xbe::XMLMessageEvent(msg)));
        incSentMessages();
    }
}

void PingPong::sendPong(const tests::xbe::PingEvent& m) {
    LOG_DEBUG("sending pong " << (_sentMessages+1));

    // generate a new PingEvent and send it to 'out'
    xbemsg::header_t hdr(_to, _from);
    xbemsg::body_t body;
    body.any().push_back(body.dom_document().createElementNS(xml::string("http://www.xenbee.net/schema/2008/02/pingpong").c_str(),
                                                             xml::string("Pong").c_str()));
    xbemsg::message_t msg(hdr, body);

    seda::ForwardStrategy::perform(seda::IEvent::Ptr(new ::xbe::XMLMessageEvent(msg)));
    incSentMessages();
}

void PingPong::sendPing(const tests::xbe::PongEvent& m) {
    LOG_DEBUG("sending ping " << (_sentMessages+1));

    // generate a new PingEvent and send it to 'out'
    xbemsg::header_t hdr(_to, _from);
    xbemsg::body_t body;
    body.any().push_back(body.dom_document().createElementNS(xml::string("http://www.xenbee.net/schema/2008/02/pingpong").c_str(),
                                                             xml::string("Ping").c_str()));
    xbemsg::message_t msg(hdr, body);

    seda::ForwardStrategy::perform(seda::IEvent::Ptr(new ::xbe::XMLMessageEvent(msg)));
    incSentMessages();
}

#include "XMLMessageEvent.hpp"
#include <sstream>

using namespace xbe;

XMLMessageEvent::XMLMessageEvent(const xbemsg::message_t& xbemsg)
  : _msg(xbemsg._clone()) {}

void XMLMessageEvent::message(const xbemsg::message_t& m) {
    _msg = std::auto_ptr<xbemsg::message_t>(m._clone());
}

std::string XMLMessageEvent::str() const {
  return "Message from " + _msg->header().from() + " to " + _msg->header().to();
}

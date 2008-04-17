#include "XMLMessageEvent.hpp"
#include <sstream>

using namespace xbe;

XMLMessageEvent::XMLMessageEvent(const xbemsg::message_t& xbemsg)
  : _msg(xbemsg) {}

std::string XMLMessageEvent::str() const {
  return "Message from " + _msg.header().from() + " to " + _msg.header().to();
}

#include "XMLDeserializeStrategy.hpp"
#include "MessageEvent.hpp"
#include "XMLMessageEvent.hpp"
#include <sstream>

using namespace xbe;

void XMLDeserializeStrategy::perform(const seda::IEvent::Ptr& e) const {
  const MessageEvent* msgEvent(dynamic_cast<const MessageEvent*>(e.get()));
  if (msgEvent) {
    std::istringstream is(msgEvent->message());
    try {
      std::auto_ptr<xbemsg::message_t> msg = xbemsg::message(is);
      seda::IEvent::Ptr xmlMsg(new XMLMessageEvent(*msg));
      seda::StrategyDecorator::perform(xmlMsg);
    } catch (const xml_schema::exception& ex) {
      LOG_WARN("throwing away invalid message: " << ex);
    }
  } else {
    LOG_WARN("throwing away non-MessageEvent: " << e);
  }
}

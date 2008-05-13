#include "EventFactory.hpp"

#include <mqs/Destination.hpp>

#include "MessageEvent.hpp"
#include "ErrorEvent.hpp"

using namespace xbe;
using namespace seda;

const EventFactory& EventFactory::instance() {
  static EventFactory instance;
  return instance;
}

EventFactory::EventFactory() : XBE_INIT_LOGGER("xbe.eventFactory") {}
EventFactory::~EventFactory() {}

IEvent::Ptr EventFactory::newEvent(const cms::Message* m) const throw (UnknownConversion) {
  // try to create text from the message
  const cms::TextMessage *txtMsg = dynamic_cast<const cms::TextMessage*>(m);
  if (!txtMsg) {
    throw UnknownConversion("cannot transform generic cms::Message into event");
  } else {
    return newEvent(txtMsg);
  }

}

IEvent::Ptr EventFactory::newEvent(const cms::TextMessage* m) const {
  // build source and destination from message
  XBE_LOG_DEBUG("msg has reply-to: " << (m->getCMSReplyTo() != 0 ? "true" : "false"));
  XBE_LOG_DEBUG("msg has dst: " << (m->getCMSDestination() != 0 ? "true" : "false"));
  mqs::Destination src(m->getCMSReplyTo());
  mqs::Destination dst(m->getCMSDestination());
  MessageEvent *me(new MessageEvent(m->getText(), src, dst));
  me->id(m->getCMSMessageID());
  return seda::IEvent::Ptr(me);
}

IEvent::Ptr EventFactory::newEvent(const cms::CMSException& ex) const {
  return seda::IEvent::Ptr(new ErrorEvent(ex.getMessage(), ex.getStackTraceString()));
}

IEvent::Ptr EventFactory::newEvent(const std::exception& ex) const {
  return seda::IEvent::Ptr(new ErrorEvent(ex.what()));
}


SystemEvent::Ptr EventFactory::newErrorEvent(const std::string& reason, const std::string& additionalData) const {
    return SystemEvent::Ptr(new ErrorEvent(reason, additionalData));
}

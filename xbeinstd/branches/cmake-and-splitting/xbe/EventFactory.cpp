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

EventFactory::EventFactory() : INIT_LOGGER("xbe.eventFactory") {}
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
  LOG_DEBUG("msg has reply-to: " << (m->getCMSReplyTo() != 0 ? "true" : "false"));
  LOG_DEBUG("msg has dst: " << (m->getCMSDestination() != 0 ? "true" : "false"));
  mqs::Destination src(m->getCMSReplyTo());
  mqs::Destination dst(m->getCMSDestination());
  MessageEvent *me(new MessageEvent(m->getText(), src, dst));
  me->id(m->getCMSMessageID());
  return seda::IEvent::Ptr(me);
}

IEvent::Ptr EventFactory::newEvent(const cms::CMSException& ex) const {
  return seda::IEvent::Ptr(new ErrorEvent(ex.getMessage(), ex.getStackTraceString()));
}
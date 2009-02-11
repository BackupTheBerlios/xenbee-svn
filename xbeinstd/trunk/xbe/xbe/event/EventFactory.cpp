#include "EventFactory.hpp"

#include <mqs/Destination.hpp>

#include "MessageEvent.hpp"
#include "ErrorEvent.hpp"

using namespace xbe;
using namespace xbe::event;
using namespace seda;

const EventFactory& EventFactory::instance() {
  static EventFactory instance;
  return instance;
}

EventFactory::EventFactory() : XBE_INIT_LOGGER("xbe.eventFactory") {}
EventFactory::~EventFactory() {}

IEvent::Ptr EventFactory::newEvent(const mqs::Message &m) const throw (UnknownConversion) {
  XBE_LOG_DEBUG("msg has reply-to: " << ((m.from().isValid()) ? "true" : "false"));
  XBE_LOG_DEBUG("msg has dst: " << (m->to().isValid() ? "true" : "false"));
  MessageEvent *me(new MessageEvent(m.body(), m.from(), m.to()));
  me->id(m.id());
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

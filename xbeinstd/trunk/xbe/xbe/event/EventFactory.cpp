#include "EventFactory.hpp"

#include <mqs/Destination.hpp>

#include "EncodedMessageEvent.hpp"
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
    EncodedMessageEvent::Ptr eme(new EncodedMessageEvent(m.body(), m.from(), m.to()));
    eme->id(m.id());
    return eme;
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

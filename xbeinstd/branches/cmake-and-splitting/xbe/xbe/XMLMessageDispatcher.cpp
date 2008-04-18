#include "XMLMessageDispatcher.hpp"

using namespace xbe;

void XMLMessageDispatcher::perform(const seda::IEvent::Ptr& e) const {
    const XMLMessageEvent* xmlEvent(dynamic_cast<const XMLMessageEvent*>(e.get()));
    if (xmlEvent) {
        const_cast<XMLMessageDispatcher*>(this)->dispatch(xmlEvent->message());
        seda::StrategyDecorator::perform(e);
    } else {
        LOG_WARN("throwing away non-XMLMessageEvent: " << e);
    }
}

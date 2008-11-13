#include <fstream>
#include <sstream>

#include "event/XMLEvent.hpp"
#include "event/MessageEvent.hpp"
#include "XMLSerializeStrategy.hpp"
#include "XbeLibUtils.hpp"

using namespace xbe;
using namespace xbe::event;

void XMLSerializeStrategy::perform(const seda::IEvent::Ptr& e) const {
    const XMLEvent* xmlEvent(dynamic_cast<const XMLEvent*>(e.get()));
    if (xmlEvent) {
        std::ostringstream oss;
        XbeLibUtils::serialize(oss, xmlEvent->payload());
        std::ofstream out("resources/test1.xml");
        XbeLibUtils::serialize(out, xmlEvent->payload());

        MessageEvent *msgEvent(new MessageEvent(oss.str(),
                                                mqs::Destination(xmlEvent->to()),
                                                mqs::Destination(xmlEvent->from())));
        seda::StrategyDecorator::perform(seda::IEvent::Ptr(msgEvent));
    } else {
        XBE_LOG_WARN("throwing away non-XMLEvent: " << e);
    }
}

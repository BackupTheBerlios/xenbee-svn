#include "XMLSerializeStrategy.hpp"
#include "MessageEvent.hpp"
#include "XMLMessageEvent.hpp"
#include "XbeLibUtils.hpp"
#include <sstream>

using namespace xbe;

void XMLSerializeStrategy::perform(const seda::IEvent::Ptr& e) const {
  const XMLMessageEvent* xmlEvent(dynamic_cast<const XMLMessageEvent*>(e.get()));
  if (xmlEvent) {
    std::ostringstream oss;
    xbemsg::message(oss, xmlEvent->message(), XbeLibUtils::namespace_infomap());
    seda::IEvent::Ptr msgEvent(new MessageEvent(oss.str()));
    
    seda::StrategyDecorator::perform(msgEvent);
  } else {
    LOG_WARN("throwing away non-XMLMessageEvent: " << e);
  }
}

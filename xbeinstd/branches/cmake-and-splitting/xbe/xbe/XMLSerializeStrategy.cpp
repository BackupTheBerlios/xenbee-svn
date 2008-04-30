#include "XMLSerializeStrategy.hpp"
#include "MessageEvent.hpp"
#include "XMLMessageEvent.hpp"
#include "XbeLibUtils.hpp"
#include <sstream>

using namespace xbe;

void XMLSerializeStrategy::perform(const seda::IEvent::Ptr& e) const {
  const XMLMessageEvent* xmlEvent(dynamic_cast<const XMLMessageEvent*>(e.get()));
  if (xmlEvent) {
      LOG_DEBUG("length of body: " << xmlEvent->message().body().any().size());
    std::ostringstream oss;
    xbemsg::message(oss, xmlEvent->message(), XbeLibUtils::namespace_infomap());
    MessageEvent *msgEvent(new MessageEvent(oss.str(),
                                            mqs::Destination(xmlEvent->message().header().to()),
                                            mqs::Destination(xmlEvent->message().header().from())));
    seda::StrategyDecorator::perform(seda::IEvent::Ptr(msgEvent));
  } else {
    LOG_WARN("throwing away non-XMLMessageEvent: " << e);
  }
}

#include <sstream>

#include <xercesc/dom/DOM.hpp>
#include <xsd/cxx/xml/dom/auto-ptr.hxx>
#include <xsd/cxx/tree/error-handler.hxx>

#include "XbeLibUtils.hpp"
#include "XMLDeserializeStrategy.hpp"
#include "MessageEvent.hpp"
#include "XMLEvent.hpp"

using namespace xbe;

void XMLDeserializeStrategy::perform(const seda::IEvent::Ptr& e) const {
    const MessageEvent* msgEvent(dynamic_cast<const MessageEvent*>(e.get()));
    if (msgEvent) {
        std::istringstream is(msgEvent->message());
        try {
            xsd::cxx::xml::dom::auto_ptr<xercesc::DOMDocument> doc(XbeLibUtils::parse(is, "", false));
            seda::IEvent::Ptr xmlMsg(new XMLEvent(msgEvent->destination().str(), msgEvent->source().str(), doc));
            seda::StrategyDecorator::perform(xmlMsg);
        } catch (const std::exception& ex) {
            XBE_LOG_WARN("throwing away invalid message: " << ex.what());
        }
    } else {
        XBE_LOG_WARN("throwing away non-MessageEvent: " << e);
    }
}

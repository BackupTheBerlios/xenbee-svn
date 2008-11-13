#ifndef XBE_XML_DATA_BINDER_HPP
#define XBE_XML_DATA_BINDER_HPP 1

#include <seda/IEvent.hpp>
#include <seda/StrategyDecorator.hpp>

#include <xbe/common.hpp>
#include <xbe/XbeLibUtils.hpp>
#include <xbe/event/ObjectEvent.hpp>
#include <xbe/event/XMLEvent.hpp>

namespace xbe {
    /** Transforms xml messages into xml-object messages using xsd's generated classes. */
    template <class T, typename F>
    class XMLDataBinder : public seda::StrategyDecorator {
        public:
            typedef T xml_object_type;
            typedef F xml_object_parser;

            XMLDataBinder(const seda::Strategy::Ptr& decorated)
                : seda::StrategyDecorator(decorated->name()+".xml-binder", decorated),
                XBE_INIT_LOGGER(decorated->name()+".xml-binder") {}
            virtual ~XMLDataBinder() {}

            virtual void perform(const seda::IEvent::Ptr& e) const {
                const xbe::event::XMLEvent* xmlEvent(dynamic_cast<const xbe::event::XMLEvent*>(e.get()));
                if (xmlEvent) {
                    seda::StrategyDecorator::perform(seda::IEvent::Ptr(
                                new xbe::event::ObjectEvent<xml_object_type>(xmlEvent->to(),
                                    xmlEvent->from(),
                                    xml_object_parser()(xmlEvent->payload(), (xml_schema::flags)0, XbeLibUtils::schema_properties())
                                )));
                } else {
                    XBE_LOG_WARN("throwing away non-XMLEvent: " << e);
                }
            }
        private:
            XBE_DECLARE_LOGGER();
    };
}

#endif // !XBE_XML_DATA_BINDER_HPP

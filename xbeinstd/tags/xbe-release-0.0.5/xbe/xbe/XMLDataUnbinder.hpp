#ifndef XBE_XML_DATA_UNBINDER_HPP
#define XBE_XML_DATA_UNBINDER_HPP 1

#include <xbe/common.hpp>
#include <seda/StrategyDecorator.hpp>
#include <xbe/ObjectEvent.hpp>
#include <xbe/XMLEvent.hpp>

namespace xbe {
    /** Transforms xbe-msg objects back to DOMDocuments. */
    template <class T, class S>
        class XMLDataUnbinder : public seda::StrategyDecorator {
            public:
                typedef T xml_object_type;
                typedef S xml_object_serializer;

                XMLDataUnbinder(const seda::Strategy::Ptr& decorated)
                    : seda::StrategyDecorator(decorated->name()+".xml-unbinder", decorated),
                    XBE_INIT_LOGGER(decorated->name()+".xml-unbinder") {}
                virtual ~XMLDataUnbinder() {}

                virtual void perform(const seda::IEvent::Ptr& e) const {
                    ObjectEvent<xml_object_type>* objectEvent(dynamic_cast<ObjectEvent<xml_object_type>* >(e.get()));
                    if (objectEvent) {
                        ::xml_schema::dom::auto_ptr< ::xercesc::DOMDocument > doc(xml_object_serializer()(objectEvent->object(), XbeLibUtils::namespace_infomap(), 0));
                        seda::StrategyDecorator::perform(seda::IEvent::Ptr(
                                    new XMLEvent(objectEvent->to(),
                                        objectEvent->from(),
                                        doc)
                                    ));
                    } else {
                        XBE_LOG_WARN("throwing away non-ObjectEvent: " << e);
                    }
                }
            private:
                XBE_DECLARE_LOGGER();
        };
}

#endif // !XBE_XML_DATA_UNBINDER_HPP

#ifndef XBE_XML_SERIALIZE_STRATEGY_HPP
#define XBE_XML_SERIALIZE_STRATEGY_HPP 1

#include <seda/StrategyDecorator.hpp>

namespace xbe {
    /** Encodes  XML messages into  text messages  that contain  the XML
        document.
    */
    class XMLSerializeStrategy : public seda::StrategyDecorator {
    public:
        XMLSerializeStrategy(const seda::Strategy::Ptr& decorated)
            : seda::StrategyDecorator(decorated->name()+".xml-serialize", decorated) {}
        virtual ~XMLSerializeStrategy() {}

        virtual void perform(const seda::IEvent::Ptr&) const;
    };
}

#endif // !XBE_XML_SERIALIZE_STRATEGY_HPP

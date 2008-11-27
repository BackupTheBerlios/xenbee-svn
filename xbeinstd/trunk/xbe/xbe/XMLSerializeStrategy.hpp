#ifndef XBE_XML_SERIALIZE_STRATEGY_HPP
#define XBE_XML_SERIALIZE_STRATEGY_HPP 1

#include <xbe/common.hpp>
#include <seda/StrategyDecorator.hpp>

namespace xbe {
    /** Encodes  XML messages into  text messages  that contain  the XML
        document.
    */
    class XMLSerializeStrategy : public seda::StrategyDecorator {
    public:
        XMLSerializeStrategy(const seda::Strategy::Ptr& decorated)
            : seda::StrategyDecorator(decorated->name()+".xml-serialize", decorated),
              XBE_INIT_LOGGER(decorated->name()+".xml-serialize")
        {}
        virtual ~XMLSerializeStrategy() {}

        virtual void perform(const seda::IEvent::Ptr&);
    private:
        XBE_DECLARE_LOGGER();
    };
}

#endif // !XBE_XML_SERIALIZE_STRATEGY_HPP

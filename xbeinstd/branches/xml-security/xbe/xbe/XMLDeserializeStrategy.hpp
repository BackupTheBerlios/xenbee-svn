#ifndef XBE_XML_DESERIALIZE_STRATEGY_HPP
#define XBE_XML_DESERIALIZE_STRATEGY_HPP 1

#include <xbe/common.hpp>
#include <seda/StrategyDecorator.hpp>

#include <xercesc/dom/DOM.hpp>
#include <xsd/cxx/xml/dom/auto-ptr.hxx>
#include <xsd/cxx/tree/error-handler.hxx>

namespace xbe {
    /** Decodes  text messages  that contain  an XML  document  into XML
        messages.
    */
    class XMLDeserializeStrategy : public seda::StrategyDecorator {
    public:
        XMLDeserializeStrategy(const seda::Strategy::Ptr& s);
        virtual ~XMLDeserializeStrategy() {}

        virtual void perform(const seda::IEvent::Ptr&) const;
    private:
        XBE_DECLARE_LOGGER();
        xsd::cxx::xml::dom::auto_ptr<xercesc::DOMBuilder> parser;
        xsd::cxx::tree::error_handler<char> eh;
    };
}

#endif // !XBE_XML_DESERIALIZE_STRATEGY_HPP

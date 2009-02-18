#ifndef XBE_XBELIBUTILS_HPP
#define XBE_XBELIBUTILS_HPP 1

#include <iostream>

#include <xbe/common.hpp>
#include <xbe/XbeException.hpp>
#include <xbe/XMLParserPool.hpp>

#include <xsd/cxx/xml/dom/auto-ptr.hxx>
#include <xbe/xbe-msg.hpp>

namespace xbe {
    class XbeLibUtils {
    public:
        ~XbeLibUtils() {}

        static void initialise() throw(xbe::XbeException);
        static void terminate() throw();

        static xml_schema::namespace_infomap& namespace_infomap();
        static xml_schema::properties& schema_properties();
    
        static void serialize(std::ostream& os, const xercesc::DOMDocument& doc, const std::string& encoding = "UTF-8");
        static xsd::cxx::xml::dom::auto_ptr<xercesc::DOMDocument> parse(std::istream& is, const std::string& id = "", bool validate=true);
    private:
        XbeLibUtils() {}
        static XMLParserPool *_parserPool;
    };
}

#endif // !XBE_XBELIBUTILS_HPP

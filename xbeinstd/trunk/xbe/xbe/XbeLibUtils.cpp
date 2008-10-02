#include "XbeLibUtils.hpp"
#include "XMLParserPool.hpp"

#include <xercesc/util/PlatformUtils.hpp>
#include <xsec/utils/XSECPlatformUtils.hpp>
#ifndef XSEC_NO_XALAN
#include <xalanc/XalanTransformer/XalanTransformer.hpp>
#endif

#include <xercesc/util/PlatformUtils.hpp>
#include <xercesc/util/XMLString.hpp>
#include <xercesc/dom/DOM.hpp>
#include <xercesc/dom/DOMImplementation.hpp>
#include <xercesc/dom/DOMImplementationLS.hpp>
#include <xercesc/dom/DOMWriter.hpp>
#include <xercesc/framework/StdOutFormatTarget.hpp>
#include <xercesc/framework/LocalFileFormatTarget.hpp>
#include <xercesc/parsers/XercesDOMParser.hpp>
#include <xercesc/util/XMLUni.hpp>
#include <xercesc/framework/Wrapper4InputSource.hpp>
#include <xercesc/validators/common/Grammar.hpp>
#include <xercesc/framework/MemoryManager.hpp>
#include <xercesc/framework/XMLGrammarPool.hpp>

// Xerces-C++'s default MemoryManager/XMLGrammarPool implementations.
#include <xercesc/internal/MemoryManagerImpl.hpp>
#include <xercesc/internal/XMLGrammarPoolImpl.hpp>

#include <xercesc/util/XercesDefs.hpp>
#include <xercesc/util/OutOfMemoryException.hpp>

#include <xsd/cxx/xml/string.hxx>
#include <xsd/cxx/xml/dom/auto-ptr.hxx>
#include <xsd/cxx/xml/dom/serialization-source.hxx>
#include <xsd/cxx/xml/dom/bits/error-handler-proxy.hxx>

#include <xsd/cxx/tree/exceptions.hxx>
#include <xsd/cxx/xml/sax/std-input-source.hxx>
#include <xsd/cxx/tree/error-handler.hxx>

using namespace xbe;

#ifdef XALAN_CPP_NAMESPACE_USE
XALAN_CPP_NAMESPACE_USE
#endif

#ifdef XERCES_CPP_NAMESPACE_USE
XERCES_CPP_NAMESPACE_USE
#endif

void XbeLibUtils::initialise() throw (xbe::XbeException) {
    XMLPlatformUtils::Initialize();
#ifndef XSEC_NO_XALAN
    XalanTransformer::initialize();
#endif
    XSECPlatformUtils::Initialise(/*XSECCryptoProvider = NULL*/);

    XBE_DEFINE_LOGGER("xbe.lib.utils");

    // TODO: make this configurable
    // initalize namespace map
    xml_schema::namespace_infomap& map = namespace_infomap();
    map["xbemsg"].name = "http://www.xenbee.net/schema/2008/02/xbe-msg";
    //map["xbetest"].name = "http://www.xenbee.net/schema/2008/02/xbetest";
    //map["jsdl"].name = "http://schemas.ggf.org/jsdl/2005/11/jsdl";
    //map["jsdl-posix"].name = "http://schemas.ggf.org/jsdl/2005/11/jsdl-posix";
    //map["dsig"].name = "http://www.w3.org/2000/09/xmldsig#";
    //map["dsig"].schema = "dsig.xsd";
    //map["xenc"].name = "http://www.w3.org/2001/04/xmlenc#";

    // TODO: fix the hard-coded stuff here!!!!
    std::string schema_uri(std::string("file://") + std::string(INSTALL_PREFIX) + std::string("/etc/xbe/schema"));

    XBE_LOG_DEBUG("using schema definitions from: " << schema_uri);

    xml_schema::properties& props = schema_properties();
    props.schema_location("http://www.xenbee.net/schema/2008/02/xbe-msg",   schema_uri + "/xbe-msg.xsd");
    //props.schema_location("http://www.xenbee.net/schema/2008/02/xbetest",   schema_uri + "/xbe-test.xsd");
    props.schema_location("http://schemas.ggf.org/jsdl/2005/11/jsdl",       schema_uri + "/jsdl-schema.xsd");
    props.schema_location("http://schemas.ggf.org/jsdl/2005/11/jsdl-posix", schema_uri + "/jsdl-posix-schema.xsd");
    props.schema_location("http://www.w3.org/2000/09/xmldsig#",             schema_uri + "/dsig.xsd");
    props.schema_location("http://www.w3.org/2001/04/xmlenc#",              schema_uri + "/xenc-schema.xsd");

}

void XbeLibUtils::terminate() throw () {
    try {
        XSECPlatformUtils::Terminate();
    } catch(...) {
        // ignore
    }

#ifndef XSEC_NO_XALAN
    XalanTransformer::terminate();
#endif

    try {
        XMLPlatformUtils::Terminate();
    } catch (...) {
        // ignore!
    }
}

xml_schema::namespace_infomap& XbeLibUtils::namespace_infomap() {
    static xml_schema::namespace_infomap map;
    return map;
}

xml_schema::properties& XbeLibUtils::schema_properties() {
    static xml_schema::properties props;
    return props;
}

void XbeLibUtils::serialize(std::ostream& os,
        const xercesc::DOMDocument& doc,
        const std::string& encoding)
{
    using namespace xercesc;
    namespace xml = xsd::cxx::xml;
    namespace tree = xsd::cxx::tree;

    const XMLCh ls_id [] = 
    {
        chLatin_L, chLatin_S, chNull
    };

    // Get an implementation of the Load-Store (LS) interface.
    //
    DOMImplementation* impl (
            DOMImplementationRegistry::getDOMImplementation (ls_id));

    // Create a DOMWriter.
    //
    xml::dom::auto_ptr<DOMWriter> writer (impl->createDOMWriter ());

    // Set error handler.
    //
    tree::error_handler<char> eh;
    xml::dom::bits::error_handler_proxy<char> ehp (eh);
    writer->setErrorHandler (&ehp);

    // Set encoding.
    //
    // writer->setEncoding(xml::string (encoding).c_str ());

    // Set some generally nice features.
    //
    //writer->setFeature (XMLUni::fgDOMWRTDiscardDefaultContent, true);
    //writer->setFeature (XMLUni::fgDOMWRTFormatPrettyPrint, true);

    // Adapt ostream to format target and serialize.
    //
    xml::dom::ostream_format_target oft (os);

    writer->writeNode (&oft, doc);

    eh.throw_if_failed<tree::parsing<char> > ();
}

// Parse an XML document from the standard input stream with an
// optional resource id. Resource id is used in diagnostics as
// well as to locate schemas referenced from inside the document.
//
xsd::cxx::xml::dom::auto_ptr<xercesc::DOMDocument>
XbeLibUtils::parse (std::istream& is, const std::string& id, bool validate) {
    static XMLParserPool xmlParserPool;
    return xmlParserPool.allocate()->parse(is,id,validate);
}

#include <sstream>

#include "XbeLibUtils.hpp"
#include "XMLDeserializeStrategy.hpp"
#include "MessageEvent.hpp"
#include "XMLMessageEvent.hpp"

#include <xercesc/dom/DOM.hpp>
#include <xercesc/util/XMLUniDefs.hpp> // chLatin_*
#include <xercesc/util/PlatformUtils.hpp>
#include <xercesc/validators/common/Grammar.hpp> // xercesc::Grammar
#include <xercesc/framework/Wrapper4InputSource.hpp>

#include <xsd/cxx/xml/dom/auto-ptr.hxx>
#include <xsd/cxx/xml/dom/bits/error-handler-proxy.hxx>
#include <xsd/cxx/xml/sax/std-input-source.hxx>

#include <xsd/cxx/tree/exceptions.hxx>
#include <xsd/cxx/tree/error-handler.hxx>

using namespace xbe;

XMLDeserializeStrategy::XMLDeserializeStrategy(const seda::Strategy::Ptr& s)
    : seda::StrategyDecorator(s->name()+".xml-deserialize", s),
      XBE_INIT_LOGGER(s->name()+".xml-deserialize") {

    using namespace xercesc;
    namespace xml = xsd::cxx::xml;
    namespace tree = xsd::cxx::tree;
      

    // initialize the parser and load the schema files
    const XMLCh ls_id [] = 
        {
            chLatin_L, chLatin_S, chNull};
    
    // Get an implementation of the Load-Store (LS) interface.
    //
    DOMImplementation* impl (
                             DOMImplementationRegistry::getDOMImplementation (ls_id));
    parser = xml::dom::auto_ptr<DOMBuilder>(impl->createDOMBuilder(DOMImplementationLS::MODE_SYNCHRONOUS, 0));

    parser->setFeature (XMLUni::fgDOMComments, true);
    parser->setFeature (XMLUni::fgDOMDatatypeNormalization, true);
    parser->setFeature (XMLUni::fgDOMEntities, true);
    parser->setFeature (XMLUni::fgDOMNamespaces, true);
    parser->setFeature (XMLUni::fgDOMWhitespaceInElementContent, true);
    parser->setFeature (XMLUni::fgDOMValidation, true);
    parser->setFeature (XMLUni::fgXercesSchema, true);
    parser->setFeature (XMLUni::fgXercesSchemaFullChecking, false);

    xml::dom::bits::error_handler_proxy<char> ehp (eh);
    parser->setErrorHandler (&ehp);

    parser->loadGrammar ("file:///home/alex/tmp/xenbee/xbeinstd/branches/xml-security/xbe/etc/xbe/schema/xbe-msg.xsd", Grammar::SchemaGrammarType, true);
    parser->loadGrammar ("file:///home/alex/tmp/xenbee/xbeinstd/branches/xml-security/xbe/etc/xbe/schema/dsig.xsd", Grammar::SchemaGrammarType, true);
    parser->setFeature (XMLUni::fgXercesUseCachedGrammarInParse, true);

    parser->setFeature (XMLUni::fgXercesUserAdoptsDOMDocument, true);
}



void XMLDeserializeStrategy::perform(const seda::IEvent::Ptr& e) const {
    using namespace xercesc;
    namespace xml = xsd::cxx::xml;
    namespace tree = xsd::cxx::tree;
      
    const MessageEvent* msgEvent(dynamic_cast<const MessageEvent*>(e.get()));
    if (msgEvent) {
        std::istringstream is(msgEvent->message());
        try {
            // Wrap the standard input stream.
            //
            xml::sax::std_input_source isrc (is, "");
            Wrapper4InputSource wrap (&isrc, false);

            // Parse XML to DOM.
            //
            xml_schema::dom::auto_ptr<DOMDocument> doc (parser->parse (wrap));

            eh.throw_if_failed<tree::parsing<char> > ();

            // Parse DOM to the object model.
            //
            std::auto_ptr<xbemsg::message_t> msg = xbemsg::message(is);
            XBE_LOG_DEBUG("length of body: " << msg->body().any().size());
            seda::IEvent::Ptr xmlMsg(new XMLMessageEvent(*msg));
            seda::StrategyDecorator::perform(xmlMsg);
        } catch (const xml_schema::exception& ex) {
            XBE_LOG_WARN("throwing away invalid message: " << ex);
        }
    } else {
        XBE_LOG_WARN("throwing away non-MessageEvent: " << e);
    }
}

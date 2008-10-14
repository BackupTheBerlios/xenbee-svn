#include "XMLParserPool.hpp"

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

XMLParserPool::XMLParserPool(std::size_t maxPoolSize)
    : XBE_INIT_LOGGER("xbe.xml-parser-pool"), _poolSize(0), _maxPoolSize(maxPoolSize) {

    }

XMLParserPool::~XMLParserPool() {
    try {
        boost::unique_lock<boost::mutex> lock(_mtx);
        while (!_pool.empty()) {
            XMLParser* p(_pool.front()); _pool.pop_front();
            delete p;
        }
    } catch(...) {
        XBE_LOG_WARN("exception during ~XMLParserPool()");
    }
}

std::auto_ptr<XMLParserManager> XMLParserPool::allocate() {
    boost::unique_lock<boost::mutex> lock(_mtx);

    // check if a free parser is available
    if (_pool.size()) {
        XMLParser* parser(_pool.front()); _pool.pop_front();
        return std::auto_ptr<XMLParserManager>(new XMLParserManager(parser, this));
    } else if (_poolSize < _maxPoolSize) {
        // no free parsers available but we can still create new parsers
        XMLParser* parser(initializeNewParser());
        _poolSize++;
        return std::auto_ptr<XMLParserManager>(new XMLParserManager(parser, this));
    } else {
        // all parsers are in use and pool-size has been reached, so wait until a parser is gets freed
        while (_pool.empty()) {
            _free.wait(lock);
        }
        XMLParser* parser(_pool.front()); _pool.pop_front();
        return std::auto_ptr<XMLParserManager>(new XMLParserManager(parser, this));
    }
}

void XMLParserPool::release(XMLParser* parser) {
    boost::unique_lock<boost::mutex> lock(_mtx);
    _pool.push_back(parser);
    _free.notify_one();
}

XMLParser* XMLParserPool::initializeNewParser() const {
    return new XMLParser();
}

XMLParser::XMLParser() {
    using namespace xercesc;
    namespace xml = xsd::cxx::xml;
    namespace tree = xsd::cxx::tree;

    _memMgr = new MemoryManagerImpl();
    _grammarPool = new XMLGrammarPoolImpl(_memMgr);

    const XMLCh ls_id [] = {chLatin_L, chLatin_S, chNull};

    // Get an implementation of the Load-Store (LS) interface.
    //
    DOMImplementation* impl (
            DOMImplementationRegistry::getDOMImplementation (ls_id));

    // Create a DOMBuilder.
    //
    // TODO: make this a class-member and initialize just once
    parser = impl->createDOMBuilder(DOMImplementationLS::MODE_SYNCHRONOUS, 0, _memMgr, _grammarPool);

    // Discard comment nodes in the document.
    //
    parser->setFeature (XMLUni::fgDOMComments, false);

    // Enable datatype normalization.
    //
    parser->setFeature (XMLUni::fgDOMDatatypeNormalization, true);

    // Do not create EntityReference nodes in the DOM tree. No
    // EntityReference nodes will be created, only the nodes
    // corresponding to their fully expanded substitution text
    // will be created.
    //
    //parser->setFeature (XMLUni::fgDOMEntities, false);
    parser->setFeature (XMLUni::fgDOMEntities, true);

    // Perform Namespace processing.
    //
    parser->setFeature (XMLUni::fgDOMNamespaces, true);

    // Do not include ignorable whitespace in the DOM tree.
    //
    parser->setFeature (XMLUni::fgDOMWhitespaceInElementContent, false);

    parser->setFeature (XMLUni::fgXercesSchemaFullChecking, false);

    // We will release the DOM document ourselves.
    //
    parser->setFeature (XMLUni::fgXercesUserAdoptsDOMDocument, true);

    // Enable grammar caching and load known grammars
    parser->loadGrammar((INSTALL_PREFIX + std::string("/etc/xbe/schema/xbe-msg.xsd")).c_str(), Grammar::SchemaGrammarType, true);
    parser->loadGrammar((INSTALL_PREFIX + std::string("/etc/xbe/schema/dsig.xsd")).c_str(), Grammar::SchemaGrammarType, true);
    parser->setFeature(XMLUni::fgXercesUseCachedGrammarInParse, true);

}

XMLParser::~XMLParser() {
    delete parser;
//   delete _grammarPool;
    delete _memMgr;
}

xsd::cxx::xml::dom::auto_ptr<xercesc::DOMDocument>
XMLParser::parse (std::istream& is, const std::string& id, bool validate) {
    using namespace xercesc;
    namespace xml = xsd::cxx::xml;
    namespace tree = xsd::cxx::tree;

    // Enable/Disable validation.
    //
    parser->setFeature (XMLUni::fgDOMValidation, validate);
    parser->setFeature (XMLUni::fgXercesSchema, validate);

    // Set error handler.
    //
    tree::error_handler<char> eh;
    xml::dom::bits::error_handler_proxy<char> ehp (eh);
    parser->setErrorHandler (&ehp);

    // Prepare input stream.
    //
    xml::sax::std_input_source isrc (is, id);
    Wrapper4InputSource wrap (&isrc, false);

    xml::dom::auto_ptr<DOMDocument> doc (parser->parse (wrap));

    eh.throw_if_failed<tree::parsing<char> > ();

    return doc;
}

XMLParserManager::~XMLParserManager() {
    _pool->release(_parser);
}

#include "testsconfig.hpp"
#include "XMLSecurityLibraryTest.hpp"

#include <ostream>
#include <string>
#include <sstream>

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

#include <xercesc/util/XercesDefs.hpp>
#include <xercesc/util/OutOfMemoryException.hpp>

#include <xsec/framework/XSECProvider.hpp>
#include <xsec/framework/XSECException.hpp>
#include <xsec/xenc/XENCEncryptedData.hpp>
#include <xsec/enc/XSECCryptoException.hpp>
#include <xsec/dsig/DSIGSignature.hpp>
#include <xsec/dsig/DSIGReference.hpp>

#include <xsd/cxx/xml/string.hxx>

#include <xbe/XbeLibUtils.hpp>

#include <xsd/cxx/xml/dom/auto-ptr.hxx>
#include <xsd/cxx/xml/dom/serialization-source.hxx>
#include <xsd/cxx/xml/dom/bits/error-handler-proxy.hxx>

#include <xsd/cxx/tree/exceptions.hxx>
#include <xsd/cxx/xml/sax/std-input-source.hxx>
#include <xsd/cxx/tree/error-handler.hxx>


xsd::cxx::xml::dom::auto_ptr<xercesc::DOMDocument>
create (const std::string& root_element_name,
        const std::string& root_element_namespace = "",
        const std::string& root_element_namespace_prefix = "");

xsd::cxx::xml::dom::auto_ptr<xercesc::DOMDocument>
create (const std::string& name,
        const std::string& ns,
        const std::string& prefix)
{
    using namespace xercesc;
    namespace xml = xsd::cxx::xml;
    
    const XMLCh ls_id [] = {chLatin_L, chLatin_S, chNull};
    
    // Get an implementation of the Load-Store (LS) interface.
    //
    DOMImplementation* impl (DOMImplementationRegistry::getDOMImplementation (ls_id));
    xml::dom::auto_ptr<DOMDocument> doc (impl->createDocument((ns.empty () ? 0 : xml::string (ns).c_str ()),
                                                              xml::string ((prefix.empty () ? name : prefix + ':' + name)).c_str (),
                                                              0));
    
    return doc;
}

void
serialize (std::ostream& os,
           const xercesc::DOMDocument& doc,
           const std::string& encoding = "UTF-8")
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
    //    writer->setEncoding(xml::string (encoding).c_str ());

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
parse (std::istream& is, const std::string& id, bool validate)
{
    using namespace xercesc;
    namespace xml = xsd::cxx::xml;
    namespace tree = xsd::cxx::tree;

    const XMLCh ls_id [] = 
        {
            chLatin_L, chLatin_S, chNull};

    // Get an implementation of the Load-Store (LS) interface.
    //
    DOMImplementation* impl (
                             DOMImplementationRegistry::getDOMImplementation (ls_id));

    // Create a DOMBuilder.
    //
    xml::dom::auto_ptr<DOMBuilder> parser (
                                           impl->createDOMBuilder(DOMImplementationLS::MODE_SYNCHRONOUS, 0));

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

    // Enable/Disable validation.
    //
    parser->setFeature (XMLUni::fgDOMValidation, validate);
    parser->setFeature (XMLUni::fgXercesSchema, validate);
    parser->setFeature (XMLUni::fgXercesSchemaFullChecking, false);

    // We will release the DOM document ourselves.
    //
    parser->setFeature (XMLUni::fgXercesUserAdoptsDOMDocument, true);

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

xsd::cxx::xml::dom::auto_ptr<xercesc::DOMDocument>
createExample (const std::string& text) {
    xsd::cxx::xml::dom::auto_ptr<xercesc::DOMDocument> doc(create("message", "http://www.xenbee.net/schema/2008/02/xbe-msg", "xbemsg"));
    DOMElement* root = doc->getDocumentElement();

    root->setAttributeNS(xml::string("http://www.w3.org/2000/xmlns/").c_str(),
                         xml::string("xmlns:xbemsg").c_str(),
                         xml::string("http://www.xenbee.net/schema/2008/02/xbe-msg").c_str());

    /* HEADER */
    DOMElement*  hdrElem = doc->createElementNS(xml::string("http://www.xenbee.net/schema/2008/02/xbe-msg").c_str(),
                                                xml::string("xbemsg:header").c_str());
    root->appendChild(hdrElem);

    DOMElement*  toElem = doc->createElementNS(xml::string("http://www.xenbee.net/schema/2008/02/xbe-msg").c_str(),
                                               xml::string("xbemsg:to").c_str());
    hdrElem->appendChild(toElem);
    DOMText*    toTxt   = doc->createTextNode(xml::string("foo.bar").c_str());
    toElem->appendChild(toTxt);
    
    DOMElement*  fromElem = doc->createElementNS(xml::string("http://www.xenbee.net/schema/2008/02/xbe-msg").c_str(),
                                                 xml::string("xbemsg:from").c_str());
    hdrElem->appendChild(fromElem);
    DOMText*    fromTxt   = doc->createTextNode(xml::string("foo.bar").c_str());
    fromElem->appendChild(fromTxt);

    /* BODY */
    DOMElement*  bodyElem = doc->createElementNS(xml::string("http://www.xenbee.net/schema/2008/02/xbe-msg").c_str(),
                                                 xml::string("xbemsg:body").c_str());
    root->appendChild(bodyElem);

    /* some example content */
    DOMElement*  exampleContentElem = doc->createElementNS(xml::string("http://www.example.com/text").c_str(), xml::string("text").c_str());
    exampleContentElem->setAttributeNS(xml::string("http://www.w3.org/2000/xmlns/").c_str(),
                                      xml::string("xmlns").c_str(),
                                      xml::string("http://www.example.com/text").c_str());
    bodyElem->appendChild(exampleContentElem);
    
    DOMText*    exampleContentTxt   = doc->createTextNode(xml::string(text).c_str());
    exampleContentElem->appendChild(exampleContentTxt);
    return doc;
}

XERCES_CPP_NAMESPACE_USE

using namespace xbe::tests;
namespace xml = xsd::cxx::xml;

CPPUNIT_TEST_SUITE_REGISTRATION( XMLSecurityLibraryTest );

XMLSecurityLibraryTest::XMLSecurityLibraryTest()
    : XBE_INIT_LOGGER("tests.xbe.xml-security-library")
{}

void
XMLSecurityLibraryTest::setUp() {
    // XMLPlatformUtils::Initialize();
    XbeLibUtils::initialise();
}

void
XMLSecurityLibraryTest::tearDown() {
    // XMLPlatformUtils::Terminate();
    XbeLibUtils::terminate();
}

void XMLSecurityLibraryTest::testSignHomePageExample() {
    XBE_LOG_DEBUG("running the simple signing example from the xml-security homepage...");

    xsd::cxx::xml::dom::auto_ptr<xercesc::DOMDocument> doc(create("company", "", ""));
    DOMElement* rootElem = doc->getDocumentElement();

    DOMElement*  prodElem = doc->createElement(xml::string("product").c_str());
    rootElem->appendChild(prodElem);

    DOMText*    prodDataVal = doc->createTextNode(xml::string("Xerces-C").c_str());
    prodElem->appendChild(prodDataVal);

    DOMElement*  catElem = doc->createElement(xml::string("category").c_str());
    rootElem->appendChild(catElem);

    catElem->setAttribute(xml::string("idea").c_str(), xml::string("great").c_str());

    DOMText*    catDataVal = doc->createTextNode(xml::string("XML Parsing Tools").c_str());
    catElem->appendChild(catDataVal);

    DOMElement*  devByElem = doc->createElement(xml::string("developedBy").c_str());
    rootElem->appendChild(devByElem);

    DOMText*    devByDataVal = doc->createTextNode(xml::string("Apache Software Foundation").c_str());
    devByElem->appendChild(devByDataVal);
    
    XSECProvider prov;
    DSIGSignature *sig;
    DOMElement *sigNode;

    sig = prov.newSignature();
    sig->setDSIGNSPrefix(xml::string("dsig").c_str());

    // Use it to create a blank signature DOM structure from the doc

    sigNode = sig->createBlankSignature(doc.get(),
                                        CANON_C14N_NOC,
                                        SIGNATURE_HMAC,
                                        HASH_SHA1);
    // Insert the signature DOM nodes into the doc

    rootElem->appendChild(sigNode);

    // Create an envelope reference for the text to be signed
    DSIGReference * ref = sig->createReference(xml::string("").c_str());
    ref->appendEnvelopedSignatureTransform();

    // Set the HMAC Key to be the string "secret"

    XSECCryptoKeyHMAC *hmacKey = XSECPlatformUtils::g_cryptoProvider->keyHMAC();
    hmacKey->setKey((unsigned char *) "secret", strlen("secret"));
    sig->setSigningKey(hmacKey);

    // Add a KeyInfo element
    sig->appendKeyName(xml::string("The secret key is \"secret\"").c_str());

    // Sign
    XBE_LOG_DEBUG("signing the document with key \"secret\"");
    sig->sign();

    {
        std::ofstream of("resources/company-example.xml");
        serialize(of, *doc);
        XBE_LOG_DEBUG("dumped signed document to: " << "resources/company-example.xml");
    }

    DSIGSignature *sig1 = prov.newSignatureFromDOM(doc.get());
    sig1->load();

    hmacKey = XSECPlatformUtils::g_cryptoProvider->keyHMAC();
    hmacKey->setKey((unsigned char *) "secret", strlen("secret"));
    sig1->setSigningKey(hmacKey);

    XBE_LOG_DEBUG("verifying the document");
    bool isValid(sig1->verify());
    char *_errMsgs = XMLString::transcode(sig1->getErrMsgs());
    std::string errMsgs(_errMsgs);
    XMLString::release(&_errMsgs);

    prov.releaseSignature(sig);
    prov.releaseSignature(sig1);
    // Verify
    CPPUNIT_ASSERT_MESSAGE(errMsgs, isValid);

    XBE_LOG_DEBUG("document successfully validated!");
}

void
XMLSecurityLibraryTest::testParseValidateHomePageExample() {
    std::string filename("resources/company-example.xml");
    XBE_LOG_DEBUG("parsing valid message: " << filename);
    std::ifstream ifs(filename.c_str());
    xsd::cxx::xml::dom::auto_ptr<xercesc::DOMDocument> doc(parse(ifs, filename, false));

    XSECProvider prov;
    DSIGSignature *sig = prov.newSignatureFromDOM(doc.get());
    XBE_LOG_DEBUG("loading signature");
    sig->load();

    XSECCryptoKeyHMAC *hmacKey = XSECPlatformUtils::g_cryptoProvider->keyHMAC();
    hmacKey->setKey((unsigned char *) "secret", (unsigned int)strlen("secret"));
    sig->setSigningKey(hmacKey);

    XBE_LOG_DEBUG("verifying signature");
    bool isValid(sig->verify());

    if (!isValid) {
        char *_errMsgs = XMLString::transcode(sig->getErrMsgs());
        std::string errMsgs(_errMsgs);
        XMLString::release(&_errMsgs);
        CPPUNIT_ASSERT_MESSAGE(errMsgs, isValid);
    } else {
        CPPUNIT_ASSERT(isValid);
    }
    XBE_LOG_DEBUG("message is valid");
}

void
XMLSecurityLibraryTest::testSign() {
    XBE_LOG_DEBUG("signing a xbe-message document by hand");
    
    xsd::cxx::xml::dom::auto_ptr<xercesc::DOMDocument> doc(create("message", "http://www.xenbee.net/schema/2008/02/xbe-msg", "xbemsg"));
    DOMElement* root = doc->getDocumentElement();

    root->setAttributeNS(xml::string("http://www.w3.org/2000/xmlns/").c_str(),
                         xml::string("xmlns:xbemsg").c_str(),
                         xml::string("http://www.xenbee.net/schema/2008/02/xbe-msg").c_str());

    /* HEADER */
    DOMElement*  hdrElem = doc->createElementNS(xml::string("http://www.xenbee.net/schema/2008/02/xbe-msg").c_str(),
                                                xml::string("xbemsg:header").c_str());
    root->appendChild(hdrElem);

    DOMElement*  toElem = doc->createElementNS(xml::string("http://www.xenbee.net/schema/2008/02/xbe-msg").c_str(),
                                               xml::string("xbemsg:to").c_str());
    hdrElem->appendChild(toElem);
    DOMText*    toTxt   = doc->createTextNode(xml::string("foo.bar").c_str());
    toElem->appendChild(toTxt);
    
    DOMElement*  fromElem = doc->createElementNS(xml::string("http://www.xenbee.net/schema/2008/02/xbe-msg").c_str(),
                                                 xml::string("xbemsg:from").c_str());
    hdrElem->appendChild(fromElem);
    DOMText*    fromTxt   = doc->createTextNode(xml::string("foo.bar").c_str());
    fromElem->appendChild(fromTxt);

    /* BODY */
    DOMElement*  bodyElem = doc->createElementNS(xml::string("http://www.xenbee.net/schema/2008/02/xbe-msg").c_str(),
                                                 xml::string("xbemsg:body").c_str());
    root->appendChild(bodyElem);

    /* some example content */
    DOMElement*  exampleContentElem = doc->createElementNS(xml::string("http://www.example.com/text").c_str(), xml::string("text").c_str());
    exampleContentElem->setAttributeNS(xml::string("http://www.w3.org/2000/xmlns/").c_str(),
                                      xml::string("xmlns").c_str(),
                                      xml::string("http://www.example.com/text").c_str());
    bodyElem->appendChild(exampleContentElem);
    
    DOMText*    exampleContentTxt   = doc->createTextNode(xml::string("Hello World!").c_str());
    exampleContentElem->appendChild(exampleContentTxt);
    
    XSECProvider prov;
    DSIGSignature *sig;
    DOMElement *sigNode;

    sig = prov.newSignature();
    sig->setDSIGNSPrefix(xml::string("dsig").c_str());

    // Use it to create a blank signature DOM structure from the doc

    sigNode = sig->createBlankSignature(doc.get(),
                                        CANON_C14N_NOC,
                                        SIGNATURE_HMAC,
                                        HASH_SHA1);
    // Insert the signature DOM nodes into the doc

    hdrElem->appendChild(sigNode);
    //    doc->normalizeDocument();
    // Create an envelope reference for the text to be signed
    DSIGReference * ref = sig->createReference(xml::string("").c_str());
    ref->appendEnvelopedSignatureTransform();

    // Set the HMAC Key to be the string "secret"
    XSECCryptoKeyHMAC *hmacKey = XSECPlatformUtils::g_cryptoProvider->keyHMAC();
    hmacKey->setKey((unsigned char *) "secret", (unsigned int)strlen("secret"));
    sig->setSigningKey(hmacKey);

    // Add a KeyInfo element
    sig->appendKeyName(xml::string("The secret key is \"secret\"").c_str());

    // Sign
    XBE_LOG_DEBUG("signing the document");
    sig->sign();

    {
        std::ofstream of("resources/xbe-message-example.xml");
        serialize(of, *doc);
        XBE_LOG_DEBUG("dumped signed document to: " << "resources/xbe-message-example.xml");
    }

    DSIGSignature *sig1 = prov.newSignatureFromDOM(doc.get());
    sig1->load();

    hmacKey = XSECPlatformUtils::g_cryptoProvider->keyHMAC();
    hmacKey->setKey((unsigned char *) "secret", strlen("secret"));
    sig1->setSigningKey(hmacKey);

    XBE_LOG_DEBUG("validating the document");
    bool isValid(sig1->verify());
    char *_errMsgs = XMLString::transcode(sig1->getErrMsgs());
    std::string errMsgs(_errMsgs);
    XMLString::release(&_errMsgs);

    prov.releaseSignature(sig);
    prov.releaseSignature(sig1);
    // Verify
    CPPUNIT_ASSERT_MESSAGE(errMsgs, isValid);

    XBE_LOG_DEBUG("the message is valid!");
}

void
XMLSecurityLibraryTest::testValidate() {
    std::string filename("resources/xbe-message-example.xml");
    XBE_LOG_DEBUG("parsing valid message: " << filename);
    std::ifstream ifs(filename.c_str());
    xsd::cxx::xml::dom::auto_ptr<xercesc::DOMDocument> doc(parse(ifs, filename, false));

    XSECProvider prov;
    DSIGSignature *sig = prov.newSignatureFromDOM(doc.get());
    XBE_LOG_DEBUG("loading signature");
    sig->load();

    XSECCryptoKeyHMAC *hmacKey = XSECPlatformUtils::g_cryptoProvider->keyHMAC();
    hmacKey->setKey((unsigned char *) "secret", (unsigned int)strlen("secret"));
    sig->setSigningKey(hmacKey);

    XBE_LOG_DEBUG("verifying signature");
    bool isValid(sig->verify());

    if (!isValid) {
        char *_errMsgs = XMLString::transcode(sig->getErrMsgs());
        std::string errMsgs(_errMsgs);
        XMLString::release(&_errMsgs);
        CPPUNIT_ASSERT_MESSAGE(errMsgs, isValid);
    } else {
        CPPUNIT_ASSERT(isValid);
    }
    XBE_LOG_DEBUG("message is valid");
}

void
XMLSecurityLibraryTest::testParseValidateValidSignature() {
    std::string filename("resources/signed-message-checked-valid.xml");
    XBE_LOG_DEBUG("parsing valid message: " << filename);
    std::ifstream ifs(filename.c_str());
    xsd::cxx::xml::dom::auto_ptr<xercesc::DOMDocument> doc(parse(ifs, filename, false));

    XSECProvider prov;
    DSIGSignature *sig = prov.newSignatureFromDOM(doc.get());
    XBE_LOG_DEBUG("loading signature");
    sig->load();

    XSECCryptoKeyHMAC *hmacKey = XSECPlatformUtils::g_cryptoProvider->keyHMAC();
    hmacKey->setKey((unsigned char *) "secret", (unsigned int)strlen("secret"));
    sig->setSigningKey(hmacKey);

    XBE_LOG_DEBUG("verifying signature");
    bool isValid(sig->verify());

    if (!isValid) {
        char *_errMsgs = XMLString::transcode(sig->getErrMsgs());
        std::string errMsgs(_errMsgs);
        XMLString::release(&_errMsgs);
        CPPUNIT_ASSERT_MESSAGE(errMsgs, isValid);
    } else {
        CPPUNIT_ASSERT(isValid);
    }
    XBE_LOG_DEBUG("message is valid");
}

void
XMLSecurityLibraryTest::testParseValidateInvalidSignature() {
    std::string filename("resources/signed-message-checked-invalid.xml");
    XBE_LOG_DEBUG("parsing invalid message: " << filename);
    std::ifstream ifs(filename.c_str());
    xsd::cxx::xml::dom::auto_ptr<xercesc::DOMDocument> doc(parse(ifs, filename, false));
    
    XSECProvider prov;
    DSIGSignature *sig = prov.newSignatureFromDOM(doc.get());
    XBE_LOG_DEBUG("loading signature");
    sig->load();

    XSECCryptoKeyHMAC *hmacKey = XSECPlatformUtils::g_cryptoProvider->keyHMAC();
    hmacKey->setKey((unsigned char *) "secret", strlen("secret"));
    sig->setSigningKey(hmacKey);

    XBE_LOG_DEBUG("verifying signature");
    bool isValid(sig->verify());
    CPPUNIT_ASSERT(! isValid);
    XBE_LOG_DEBUG("message is invalid");
}

void
XMLSecurityLibraryTest::testEncrypt() {
    XBE_LOG_DEBUG("encrypting a xbe-message document by hand");
    
    xsd::cxx::xml::dom::auto_ptr<xercesc::DOMDocument> doc(create("message", "http://www.xenbee.net/schema/2008/02/xbe-msg", "xbemsg"));
    DOMElement* root = doc->getDocumentElement();

    root->setAttributeNS(xml::string("http://www.w3.org/2000/xmlns/").c_str(),
                         xml::string("xmlns:xbemsg").c_str(),
                         xml::string("http://www.xenbee.net/schema/2008/02/xbe-msg").c_str());

    /* HEADER */
    DOMElement*  hdrElem = doc->createElementNS(xml::string("http://www.xenbee.net/schema/2008/02/xbe-msg").c_str(),
                                                xml::string("xbemsg:header").c_str());
    root->appendChild(hdrElem);

    DOMElement*  toElem = doc->createElementNS(xml::string("http://www.xenbee.net/schema/2008/02/xbe-msg").c_str(),
                                               xml::string("xbemsg:to").c_str());
    hdrElem->appendChild(toElem);
    DOMText*    toTxt   = doc->createTextNode(xml::string("foo.bar").c_str());
    toElem->appendChild(toTxt);
    
    DOMElement*  fromElem = doc->createElementNS(xml::string("http://www.xenbee.net/schema/2008/02/xbe-msg").c_str(),
                                                 xml::string("xbemsg:from").c_str());
    hdrElem->appendChild(fromElem);
    DOMText*    fromTxt   = doc->createTextNode(xml::string("foo.bar").c_str());
    fromElem->appendChild(fromTxt);

    /* BODY */
    DOMElement*  bodyElem = doc->createElementNS(xml::string("http://www.xenbee.net/schema/2008/02/xbe-msg").c_str(),
                                                 xml::string("xbemsg:body").c_str());
    root->appendChild(bodyElem);

    /* some example content */
    DOMElement*  exampleContentElem = doc->createElementNS(xml::string("http://www.example.com/text").c_str(), xml::string("text").c_str());
    exampleContentElem->setAttributeNS(xml::string("http://www.w3.org/2000/xmlns/").c_str(),
                                      xml::string("xmlns").c_str(),
                                      xml::string("http://www.example.com/text").c_str());
    bodyElem->appendChild(exampleContentElem);
    
    DOMText*    exampleContentTxt   = doc->createTextNode(xml::string("Hello World!").c_str());
    exampleContentElem->appendChild(exampleContentTxt);

    
}

void
XMLSecurityLibraryTest::testDecrypt() {

}

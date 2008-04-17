#include "testsconfig.hpp"
#include "XMLSecurityLibraryTest.hpp"

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

#include <xercesc/util/XercesDefs.hpp>
#include <xercesc/util/OutOfMemoryException.hpp>

#include <xsec/framework/XSECProvider.hpp>
#include <xsec/framework/XSECException.hpp>
#include <xsec/enc/OpenSSL/OpenSSLCryptoProvider.hpp> // TODO: fix this!!!
#include <xsec/enc/OpenSSL/OpenSSLCryptoSymmetricKey.hpp>
#include <xsec/xenc/XENCEncryptedData.hpp>
#include <xsec/enc/XSECCryptoException.hpp>
#include <xsec/dsig/DSIGSignature.hpp>
#include <xsec/dsig/DSIGReference.hpp>

#include <xbe/XbeLibUtils.hpp>

XERCES_CPP_NAMESPACE_USE

using namespace xbe::tests;

// ---------------------------------------------------------------------------
//  This is a simple class that lets us do easy (though not terribly efficient)
//  trancoding of char* data to XMLCh data.
// ---------------------------------------------------------------------------
// taken from libxerces-c examples/CreateDOMDocument/CreateDOMDocument.cpp

class XStr
{   
public :
    // -----------------------------------------------------------------------
    //  Constructors and Destructor
    // -----------------------------------------------------------------------
    XStr(const char* const toTranscode)
        : fUnicodeForm(XMLString::transcode(toTranscode))
    { }

    ~XStr()
    {
        XMLString::release(&fUnicodeForm);
    }
    
    
    // -----------------------------------------------------------------------
    //  Getter methods
    // -----------------------------------------------------------------------
    const XMLCh* unicodeForm() const
    {
        return fUnicodeForm;
    }
    
private :
    // -----------------------------------------------------------------------
    //  Private data members
    //
    //  fUnicodeForm
    //      This is the Unicode XMLCh format of the string.
    // -----------------------------------------------------------------------
    XMLCh*   fUnicodeForm;
};

#define X(str) XStr(str).unicodeForm()

static void dumpXML(DOMImplementation& impl, DOMDocument& doc) {
    DOMWriter *theSerializer = impl.createDOMWriter();
    XMLFormatTarget *myFormTarget(new StdOutFormatTarget());
    theSerializer->writeNode(myFormTarget, doc);

    delete theSerializer;
    delete myFormTarget;
}

CPPUNIT_TEST_SUITE_REGISTRATION( XMLSecurityLibraryTest );

XMLSecurityLibraryTest::XMLSecurityLibraryTest()
    : INIT_LOGGER("tests.xbe.xml-security-library")
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

void
XMLSecurityLibraryTest::testSign() {
    DOMImplementation* impl =  DOMImplementationRegistry::getDOMImplementation(X("Core"));
#if 0
    DOMDocument* doc = impl->createDocument(0,                    // root element namespace URI.
                                            X("company"),         // root element name
                                            0);                   // document type object (DTD).
    DOMElement* rootElem = doc->getDocumentElement();

    DOMElement*  prodElem = doc->createElement(X("product"));
    rootElem->appendChild(prodElem);

    DOMText*    prodDataVal = doc->createTextNode(X("Xerces-C"));
    prodElem->appendChild(prodDataVal);

    DOMElement*  catElem = doc->createElement(X("category"));
    rootElem->appendChild(catElem);

    catElem->setAttribute(X("idea"), X("great"));

    DOMText*    catDataVal = doc->createTextNode(X("XML Parsing Tools"));
    catElem->appendChild(catDataVal);

    DOMElement*  devByElem = doc->createElement(X("developedBy"));
    rootElem->appendChild(devByElem);

    DOMText*    devByDataVal = doc->createTextNode(X("Apache Software Foundation"));
    devByElem->appendChild(devByDataVal);
    
    XSECProvider prov;
    DSIGSignature *sig;
    DOMElement *sigNode;

    sig = prov.newSignature();
    sig->setDSIGNSPrefix(MAKE_UNICODE_STRING("dsig")); // MAKE_UNICODE_STRING is provided by xml-security

    // Use it to create a blank signature DOM structure from the doc

    sigNode = sig->createBlankSignature(doc,
                                        CANON_C14N_COM, 
                                        SIGNATURE_HMAC, 
                                        HASH_SHA1);
    // Insert the signature DOM nodes into the doc

    rootElem->appendChild(sigNode);

    // Create an envelope reference for the text to be signed
    DSIGReference * ref = sig->createReference(MAKE_UNICODE_STRING(""));
    ref->appendEnvelopedSignatureTransform();
  
    // Set the HMAC Key to be the string "secret"

    OpenSSLCryptoProvider cryptoProvider;
    XSECCryptoKeyHMAC *hmacKey = cryptoProvider.keyHMAC();
    hmacKey->setKey((unsigned char *) "secret", strlen("secret"));
    sig->setSigningKey(hmacKey);

    // Add a KeyInfo element
    sig->appendKeyName(MAKE_UNICODE_STRING("The secret key is \"secret\""));

    // Sign

    sig->sign();

    //    dumpXML(*impl, *doc);

    DSIGSignature *sig1 = prov.newSignatureFromDOM(doc);
    sig1->load();

    hmacKey = cryptoProvider.keyHMAC();
    hmacKey->setKey((unsigned char *) "secret", strlen("secret"));
    sig1->setSigningKey(hmacKey);

    bool isValid(sig1->verify());
    char *_errMsgs = XMLString::transcode(sig1->getErrMsgs());
    std::string errMsgs(_errMsgs);
    XMLString::release(&_errMsgs);

    prov.releaseSignature(sig);
    prov.releaseSignature(sig1);
    doc->release();
    // Verify
    CPPUNIT_ASSERT_MESSAGE(errMsgs, isValid);

    LOG_DEBUG("the message is valid!");
#else
    DOMDocument* doc = impl->createDocument(X("http://www.xenbee.net/schema/2008/02/xbe"),   // root element namespace URI.
                                            X("xbe:message"),         // root element name
                                            0);                   // document type object (DTD).

    DOMElement* rootElem = doc->getDocumentElement();
    rootElem->setAttributeNS(X("http://www.w3.org/2000/xmlns/"),
                             X("xmlns:dsig"),
                             X("http://www.w3.org/2000/09/xmldsig#"));

    /* HEADER */
    DOMElement*  hdrElem = doc->createElementNS(X("http://www.xenbee.net/schema/2008/02/xbe"), X("xbe:header"));
    rootElem->appendChild(hdrElem);

    DOMElement*  toElem = doc->createElementNS(X("http://www.xenbee.net/schema/2008/02/xbe"),X("xbe:to"));
    hdrElem->appendChild(toElem);
    DOMText*    toTxt   = doc->createTextNode(X("foo.bar"));
    toElem->appendChild(toTxt);
    
    DOMElement*  fromElem = doc->createElementNS(X("http://www.xenbee.net/schema/2008/02/xbe"), X("xbe:from"));
    hdrElem->appendChild(fromElem);
    DOMText*    fromTxt   = doc->createTextNode(X("foo.bar"));
    fromElem->appendChild(fromTxt);

    /* BODY */
    DOMElement*  bodyElem = doc->createElementNS(X("http://www.xenbee.net/schema/2008/02/xbe"), X("xbe:body"));
    rootElem->appendChild(bodyElem);

    DOMElement*  errorElem = doc->createElementNS(X("http://www.xenbee.net/schema/2008/02/xbe"), X("xbe:error"));
    bodyElem->appendChild(errorElem);
    DOMElement*  errorCodeElem = doc->createElementNS(X("http://www.xenbee.net/schema/2008/02/xbe"), X("xbe:error-code"));
    errorElem->appendChild(errorCodeElem);
    
    DOMText*    errorCodeTxt   = doc->createTextNode(X("ENOERROR"));
    errorCodeElem->appendChild(errorCodeTxt);
    
    XSECProvider prov;
    DSIGSignature *sig;
    DOMElement *sigNode;

    sig = prov.newSignature();
    sig->setDSIGNSPrefix(MAKE_UNICODE_STRING("dsig")); // MAKE_UNICODE_STRING is provided by xml-security

    // Use it to create a blank signature DOM structure from the doc

    sigNode = sig->createBlankSignature(doc,
                                        CANON_C14NE_NOC,
                                        SIGNATURE_HMAC,
                                        HASH_SHA1);
    // Insert the signature DOM nodes into the doc

    hdrElem->appendChild(sigNode);
    doc->normalizeDocument();

    // Create an envelope reference for the text to be signed
    DSIGReference * ref = sig->createReference(MAKE_UNICODE_STRING(""));
    ref->appendEnvelopedSignatureTransform();
  
    // Set the HMAC Key to be the string "secret"

    OpenSSLCryptoProvider cryptoProvider;
    XSECCryptoKeyHMAC *hmacKey = cryptoProvider.keyHMAC();
    hmacKey->setKey((unsigned char *) "secret", strlen("secret"));
    sig->setSigningKey(hmacKey);

    // Add a KeyInfo element
    sig->appendKeyName(MAKE_UNICODE_STRING("The secret key is \"secret\""));

    // Sign

    sig->sign();

    dumpXML(*impl, *doc);

    DSIGSignature *sig1 = prov.newSignatureFromDOM(doc);
    sig1->load();

    hmacKey = cryptoProvider.keyHMAC();
    hmacKey->setKey((unsigned char *) "secret", strlen("secret"));
    sig1->setSigningKey(hmacKey);

    bool isValid(sig1->verify());
    char *_errMsgs = XMLString::transcode(sig1->getErrMsgs());
    std::string errMsgs(_errMsgs);
    XMLString::release(&_errMsgs);

    prov.releaseSignature(sig);
    prov.releaseSignature(sig1);
    doc->release();
    // Verify
    CPPUNIT_ASSERT_MESSAGE(errMsgs, isValid);

    LOG_DEBUG("the message is valid!");
#endif
}

void
XMLSecurityLibraryTest::testValidate() {
    LOG_DEBUG("setting up parser");
    XercesDOMParser *parser = new XercesDOMParser;
    parser->setValidationScheme(XercesDOMParser::Val_Always);
    parser->setDoNamespaces(true);
    parser->setDoSchema(true);
    parser->setValidationSchemaFullChecking(true);

    std::string filename("sig-test-5.xml");
    try {
        parser->parse(filename.c_str());
        LOG_DEBUG("parsed: " << filename);
    } catch (const DOMException& e) {
        LOG_FATAL("errors occured during parsing: " << filename);
    }

    DOMDocument *doc = parser->getDocument();
    
    XSECProvider prov;
    DSIGSignature *sig = prov.newSignatureFromDOM(doc);
    LOG_DEBUG("loading signature");
    sig->load();

    OpenSSLCryptoProvider cryptoProvider;
    XSECCryptoKeyHMAC *hmacKey = cryptoProvider.keyHMAC();
    hmacKey->setKey((unsigned char *) "secret", strlen("secret"));
    sig->setSigningKey(hmacKey);

    LOG_DEBUG("verifying signature");
    bool isValid(sig->verify());
    char *_errMsgs = XMLString::transcode(sig->getErrMsgs());
    std::string errMsgs(_errMsgs);
    XMLString::release(&_errMsgs);

    prov.releaseSignature(sig);
    doc->release();

    CPPUNIT_ASSERT_MESSAGE(errMsgs, isValid);
    LOG_DEBUG("message is valid");
}

void
XMLSecurityLibraryTest::testEncrypt() {
}

void
XMLSecurityLibraryTest::testDecrypt() {
}


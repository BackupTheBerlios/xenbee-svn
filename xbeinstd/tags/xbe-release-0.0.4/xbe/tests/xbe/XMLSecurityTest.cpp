#include "testsconfig.hpp"
#include "XMLSecurityTest.hpp"

#include <string>
#include <sstream>

#include <xercesc/util/PlatformUtils.hpp>
#include <xercesc/util/XercesDefs.hpp>

#include <xsec/framework/XSECProvider.hpp>
#include <xsec/framework/XSECException.hpp>
#include <xsec/enc/OpenSSL/OpenSSLCryptoProvider.hpp> // TODO: fix this!!!
#include <xsec/enc/OpenSSL/OpenSSLCryptoSymmetricKey.hpp>
#include <xsec/xenc/XENCEncryptedData.hpp>
#include <xsec/enc/XSECCryptoException.hpp>
#include <xsec/dsig/DSIGSignature.hpp>
#include <xsec/dsig/DSIGReference.hpp>

#include <xbe/XbeLibUtils.hpp>
#include <xbe/MessageEvent.hpp>
#include <xbe/XMLMessageEvent.hpp>

#include <xsd/cxx/xml/string.hxx>
#include <xbe/xbe-msg.hpp>

#ifdef XERCES_CPP_NAMESPACE_USE
XERCES_CPP_NAMESPACE_USE
#endif

using namespace xbe::tests;
namespace xml = xsd::cxx::xml;

CPPUNIT_TEST_SUITE_REGISTRATION( XMLSecurityTest );

XMLSecurityTest::XMLSecurityTest()
    : XBE_INIT_LOGGER("tests.xbe.xml-security")
{}

void
XMLSecurityTest::setUp() {
    XbeLibUtils::initialise();
}

void
XMLSecurityTest::tearDown() {
    XbeLibUtils::terminate();
}

void
XMLSecurityTest::testSign() {
    xbemsg::header_t hdr("tests.xbe.foo.bar", "tests.xbe.foo.bar");
    xbemsg::body_t body;

    body.any().push_back(body.dom_document().createElementNS(xml::string("http://www.xenbee.net/schema/2008/02/pingpong").c_str(),
                                                             xml::string("Ping").c_str()));
    xbemsg::message_t msg(hdr,body);

    // serialize to DOMDocument
    xml_schema::dom::auto_ptr< ::xercesc::DOMDocument > doc =
        xbemsg::message(msg, XbeLibUtils::namespace_infomap());

    ::xercesc::DOMElement *rootElem = doc->getDocumentElement();

    XSECProvider prov;
    DSIGSignature *sig;
    xercesc::DOMElement *sigNode;

    sig = prov.newSignature();
    sig->setDSIGNSPrefix(xml::string("dsig").c_str());
    //  sig->setECNSPrefix( NULL );
    //  sig->setXPFNSPrefix(NULL);
    //  sig->setPrettyPrint(false);

    // Use it to create a blank signature DOM structure from the doc

    sigNode = sig->createBlankSignature(doc.get(),
                                        CANON_C14NE_NOC,
                                        SIGNATURE_HMAC,
                                        HASH_SHA1);
  
    // Insert the signature element at the right place within the document
    // find the header DOM node
    DOMNode *hdrNode = rootElem->getFirstChild();
    CPPUNIT_ASSERT(hdrNode != 0);

    char *tmpNodeName = XMLString::transcode(hdrNode->getLocalName());
    std::string nodeName(tmpNodeName);
    XMLString::release(&tmpNodeName);

    CPPUNIT_ASSERT_EQUAL(nodeName, std::string("header"));

    hdrNode->appendChild(sigNode);
    doc->normalizeDocument();

    // Create an envelope reference for the text to be signed
    DSIGReference * ref = sig->createReference(xml::string("").c_str());
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
  
    xbemsg::message_t signed_msg(*rootElem);
    std::ostringstream oss;
    xbemsg::message(oss, signed_msg, XbeLibUtils::namespace_infomap());

    // write to an xml file
    //   {
    //         std::ofstream ofs("sig-test-2.xml");
    //         ofs << oss.str();
    //   }
    XBE_LOG_DEBUG(oss.str());

    //   std::string expected_digest("6gEokD/uXFJHZdGdup83UEJAL7U=\n");
    //   std::string expected_sigval("t9LLbEU8GHtWrrx+qWTWWujTGEY=\n");

    //   CPPUNIT_ASSERT_EQUAL(expected_digest,
    // 		       signed_msg.header().Signature().get().SignedInfo().Reference().begin()->DigestValue().encode());
    //   CPPUNIT_ASSERT_EQUAL(expected_sigval,
    // 		       signed_msg.header().Signature().get().SignatureValue().encode());
}

void
XMLSecurityTest::testValidate() {
    xml_schema::properties& props(XbeLibUtils::schema_properties());
    
    try {
        // parse the xbe message
        std::auto_ptr<xbemsg::message_t> msg = xbemsg::message("resources/signed-message-1.xml",
                                                               xml_schema::flags::dont_initialize | xml_schema::flags::keep_dom,
                                                               props);

        // serialize to DOMDocument
        xml_schema::dom::auto_ptr< ::xercesc::DOMDocument > doc =
            xbemsg::message(*msg, XbeLibUtils::namespace_infomap());
    
        XSECProvider prov;
        DSIGSignature *sig = prov.newSignatureFromDOM(doc.get());
        sig->load();

        // Set the HMAC Key to be the string "secret"
        OpenSSLCryptoProvider cryptoProvider;
        XSECCryptoKeyHMAC *hmacKey = cryptoProvider.keyHMAC();
        hmacKey->setKey((unsigned char*)"secret", strlen("secret"));
        sig->setSigningKey(hmacKey);

        bool isValid(sig->verify());
        char *errMsgs = XMLString::transcode(sig->getErrMsgs());
        // Verify
        CPPUNIT_ASSERT_MESSAGE(errMsgs, isValid);
        XMLString::release(&errMsgs);

        prov.releaseSignature(sig);
    } catch (const std::exception& e) {
        CPPUNIT_ASSERT_MESSAGE(e.what(), false);
    }
}

void
XMLSecurityTest::testEncrypt() {
    //   xbemsg::body_t unenc_body;
    //   xbemsg::error_t error(xbemsg::ErrorCode(xbemsg::ErrorCode::ENOERROR));
    //   unenc_body.error().set(error);

    //   /********************
    //    * Encrypt the body
    //    ********************/
  
    //   // serialize to DOMDocument
    //   xml_schema::dom::auto_ptr< ::xercesc::DOMDocument > doc =
    //       xbemsg::body(unenc_body, XbeLibUtils::namespace_infomap());

    //   /* Create the cipher object that we need */
    //   XSECProvider prov;
    //   XENCCipher *cipher;

    //   cipher = prov.newCipher(doc.get());

    //   // now generate a key that we can use for encryption
    //   // we need 24 bytes for the 192 bit encryption algorithm
    //   unsigned char keyBuf[24];
    //   for (std::size_t i = 0; i < 24; ++i)
    //     keyBuf[i] = i;

    //   /* Wrap this in a Symmetric 3DES key */
    //   OpenSSLCryptoSymmetricKey * key = 
    //     new OpenSSLCryptoSymmetricKey(XSECCryptoSymmetricKey::KEY_3DES_192);
    //   key->setKey(keyBuf, 24);
    //   cipher->setKey(key);

    //   /* Encrypt the element that needs to be hidden */
    //   ::xercesc::DOMElement *bodyElem = doc->getDocumentElement();
    //   cipher->encryptElement(bodyElem, ENCRYPT_3DES_CBC);

    //   XBE_LOG_DEBUG("body element encrypted");
  
    //   /* set the Key Encryption Key, ie. encrypt the key with the string "secret" */
    //   /*
    //   OpenSSLCryptoProvider cryptoProvider;
    //   XSECCryptoKeyHMAC *hmacKey = cryptoProvider.keyHMAC();
    //   hmacKey->setKey((unsigned char *) "secret", strlen("secret"));
    //   cipher->setKEK(hmacKey);

    //   XENCEncryptedKey *encryptedKey =
    //     cipher->encryptKey(keyBuf, 24, ENCRYPT_NONE);

    //   XBE_LOG_DEBUG("encryption key encrypted");
    //   */
  
    //   /*
    //    * Add the encrypted Key to the previously created EncryptedData, which
    //    * we first retrieve from the cipher object.  This will automatically create
    //    * the appropriate <KeyInfo> element within the EncryptedData
    //    */
    //   XENCEncryptedData * encryptedData = cipher->getEncryptedData();
    //   //  encryptedData->appendEncryptedKey(encryptedKey);
    //   ::xercesc::DOMElement *encDataElem = encryptedData->getElement();
    //   xenc::EncryptedDataType encData(*encDataElem);
    //   xbemsg::body_t enc_body;
    //   enc_body.EncryptedData().set(encData);
  
    //   xbemsg::header_t hdr("tests.xbe.foo.bar", "tests.xbe.foo.bar");
    //   xbemsg::message_t msg(hdr,enc_body);

    //   XBE_LOG_DEBUG("encrypted message created");

    //   try {
    //     std::ostringstream oss;
    //     xbemsg::message(oss, msg, XbeLibUtils::namespace_infomap());
    //     XBE_LOG_DEBUG("serialized");
    //     XBE_LOG_DEBUG(oss.str());
    //   } catch(XSECCryptoException& ex) {
    //     XBE_LOG_WARN(ex.getMsg());
    //     CPPUNIT_ASSERT_MESSAGE(ex.getMsg(), false);
    //   } catch(XSECException& ex) {
    //     char *errMsg = XMLString::transcode(ex.getMsg());
    //     XBE_LOG_WARN(errMsg);
    //     XMLString::release(&errMsg);
    //     CPPUNIT_ASSERT_MESSAGE("serialization failed, see log message for more information", false);
    //   } catch (const std::exception& ex) {
    //     XBE_LOG_WARN(ex.what());
    //     CPPUNIT_ASSERT_MESSAGE(ex.what(), false);
    //   }
    //   //  CPPUNIT_ASSERT_MESSAGE("test not implemented", false);
}

void
XMLSecurityTest::testDecrypt() {
    CPPUNIT_ASSERT_MESSAGE("test not implemented", false);
}

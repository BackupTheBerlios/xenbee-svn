#include <sstream>

#include <xsec/framework/XSECProvider.hpp>
#include <xsec/framework/XSECException.hpp>
#include <xsec/xenc/XENCEncryptedData.hpp>
#include <xsec/enc/XSECCryptoException.hpp>
#include <xsec/dsig/DSIGSignature.hpp>
#include <xsec/dsig/DSIGReference.hpp>

#include <xsd/cxx/xml/string.hxx>

#include "XMLSigner.hpp"
#include "XbeLibUtils.hpp"
#include "event/XMLEvent.hpp"

using namespace xbe;
using namespace xbe::event;
using namespace xercesc;
namespace xml = xsd::cxx::xml;

void XMLSigner::perform(const seda::IEvent::Ptr& e) const {
    XMLEvent* xmlEvent(dynamic_cast<XMLEvent*>(e.get()));
    if (xmlEvent) {

        XSECProvider prov;
        DSIGSignature *sig;
        DOMElement *sigNode;
        DOMDocument *doc;
        DOMElement *hdrElem;

        doc = &(xmlEvent->payload());

        sig = prov.newSignature();
        sig->setDSIGNSPrefix(xml::string("dsig").c_str());

        // Use it to create a blank signature DOM structure from the doc
        sigNode = sig->createBlankSignature(doc,
                                            CANON_C14N_NOC,
                                            SIGNATURE_HMAC,
                                            HASH_SHA1);
        // Insert the signature DOM nodes into the doc
        doc->getDocumentElement()->appendChild(sigNode);

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

        seda::StrategyDecorator::perform(e);
    } else {
        XBE_LOG_WARN("cannot sign non-xml event: " << e);
    }
}


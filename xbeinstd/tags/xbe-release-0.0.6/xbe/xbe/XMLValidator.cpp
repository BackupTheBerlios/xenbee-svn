#include "XMLValidator.hpp"
#include "XMLEvent.hpp"
#include "XbeLibUtils.hpp"
#include <sstream>

#include <xsec/framework/XSECProvider.hpp>
#include <xsec/framework/XSECException.hpp>
#include <xsec/xenc/XENCEncryptedData.hpp>
#include <xsec/enc/XSECCryptoException.hpp>
#include <xsec/dsig/DSIGSignature.hpp>
#include <xsec/dsig/DSIGReference.hpp>

#include <xsd/cxx/xml/string.hxx>

using namespace xbe;
using namespace xercesc;
namespace xml = xsd::cxx::xml;

void ::xbe::XMLValidator::perform(const seda::IEvent::Ptr& e) const {
    XMLEvent* xmlEvent(dynamic_cast<XMLEvent*>(e.get()));
    if (xmlEvent) {

        XSECProvider prov;
        DSIGSignature *sig;
        DOMDocument *doc;

        doc = &(xmlEvent->payload());

        sig = prov.newSignatureFromDOM(doc);
        sig->load();

        // Set the HMAC Key to be the string "secret"
        XSECCryptoKeyHMAC *hmacKey = XSECPlatformUtils::g_cryptoProvider->keyHMAC();
        hmacKey->setKey((unsigned char *) "secret", (unsigned int)strlen("secret"));
        sig->setSigningKey(hmacKey);
        if (sig->verify()) {
            XBE_LOG_DEBUG("got valid message");
            // propagate event
            seda::StrategyDecorator::perform(e);
        } else {
            XBE_LOG_WARN("message could not be validated: " << e->str());
            // FIXME: maybe put that event for further analysis into another queue
            // currently, we just drop the event
        }
    } else {
        XBE_LOG_WARN("cannot sign non-xml event: " << e);
    }
}

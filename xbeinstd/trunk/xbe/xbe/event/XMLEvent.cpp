#include "XMLEvent.hpp"

using namespace xbe::event;
using namespace xercesc;
namespace xml = xsd::cxx::xml;

XMLEvent::XMLEvent(const std::string& to,
        const std::string& from,
        xsd::cxx::xml::dom::auto_ptr<DOMDocument> payload)
: _to(to), _from(from), _payload(payload) {

}

std::string XMLEvent::str() const {
    return "XMLEvent: " + from() + " -> " + to();
}

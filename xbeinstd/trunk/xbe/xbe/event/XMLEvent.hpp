#ifndef XBE_XML_EVENT_HPP
#define XBE_XML_EVENT_HPP 1

#include <seda/UserEvent.hpp>

#include <xercesc/dom/DOM.hpp>
#include <xsd/cxx/xml/dom/auto-ptr.hxx>

namespace xbe {
    namespace event {
        class XMLEvent : public seda::UserEvent {
            public:
                XMLEvent(const std::string& to,
                        const std::string& from,
                        xsd::cxx::xml::dom::auto_ptr<xercesc::DOMDocument> payload);
                virtual ~XMLEvent() {}

                virtual std::string str() const;

                const std::string& to() const { return _to; }
                const std::string& from() const { return _from; }

                const xercesc::DOMDocument& payload() const { return *_payload; }
                xercesc::DOMDocument& payload() { return *_payload; }
            private:
                std::string _to;
                std::string _from;
                xsd::cxx::xml::dom::auto_ptr<xercesc::DOMDocument> _payload;
        };
    }
}

#endif // !XBE_XML_EVENT_HPP

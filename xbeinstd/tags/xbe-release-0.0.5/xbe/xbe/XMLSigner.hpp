#ifndef XBE_XML_SIGNER_HPP
#define XBE_XML_SIGNER_HPP 1

#include <xbe/common.hpp>
#include <seda/StrategyDecorator.hpp>

namespace xbe {
    /** Signs the given document. */
    class XMLSigner : public seda::StrategyDecorator {
    public:
        XMLSigner(const seda::Strategy::Ptr& decorated)
            : seda::StrategyDecorator(decorated->name()+".xml-dsig-signer", decorated),
              XBE_INIT_LOGGER(decorated->name()+".xml-dsig-signer")
        {}
        virtual ~XMLSigner() {}

        virtual void perform(const seda::IEvent::Ptr&) const;
    private:
        XBE_DECLARE_LOGGER();
    };
}

#endif // !XBE_XML_SIGNER_HPP

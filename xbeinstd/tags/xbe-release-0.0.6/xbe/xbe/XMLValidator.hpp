#ifndef XBE_XML_VALIDATOR_HPP
#define XBE_XML_VALIDATOR_HPP 1

#include <xbe/common.hpp>
#include <seda/StrategyDecorator.hpp>

namespace xbe {
    /** Tries to validate xml events. */
    class XMLValidator : public seda::StrategyDecorator {
    public:
        XMLValidator(const seda::Strategy::Ptr& decorated)
            : seda::StrategyDecorator(decorated->name()+".xml-dsig-validator", decorated),
              XBE_INIT_LOGGER(decorated->name()+".xml-dsig-validator")
        {}
        virtual ~XMLValidator() {}

        virtual void perform(const seda::IEvent::Ptr&) const;
    private:
        XBE_DECLARE_LOGGER();
    };
}

#endif // !XBE_XML_VALIDATOR_HPP

#ifndef XBE_MESSAGE_TRANSLATOR_STRATEGY_HPP
#define XBE_MESSAGE_TRANSLATOR_STRATEGY_HPP 1

#include <xbe/common.hpp>
#include <seda/StrategyDecorator.hpp>

namespace xbe {
    /** Transforms incoming messages into application specific events. This
     * strategy works on ObjectEvents with the xbemsg type and generates events
     * for the xbeinstd application.
     *
     * The other way around also works, it takes an application specific event
     * and creates the external representation.
    */
    class MessageTranslatorStrategy : public seda::StrategyDecorator {
    public:
        XMLSerializeStrategy(const seda::Strategy::Ptr& decorated)
            : seda::StrategyDecorator(decorated->name()+".msg-translator", decorated),
              XBE_INIT_LOGGER(decorated->name()+".msg-translator")
        {}
        virtual ~XMLSerializeStrategy() {}

        virtual void perform(const seda::IEvent::Ptr&) const;
    private:
        XBE_DECLARE_LOGGER();
    };
}

#endif // !XBE_MESSAGE_TRANSLATOR_STRATEGY_HPP


#ifndef XBE_MESSAGE_TRANSLATOR_STRATEGY_HPP
#define XBE_MESSAGE_TRANSLATOR_STRATEGY_HPP 1

#include <xbe/common.hpp>
#include <xbe/XbeException.hpp>
#include <seda/StrategyDecorator.hpp>

#include <xbe/TaskData.hpp>
#include <xbe/xbe-msg.hpp>

namespace xbe {
    class TranslationError : public xbe::XbeException {
    public:
       TranslationError(const std::string &reason)
        : xbe::XbeException(reason) {} 
    };

    /** Transforms incoming messages into application specific events. This
     * strategy works on ObjectEvents with the xbemsg type and generates events
     * for the xbeinstd application.
     *
     * The other way around also works, it takes an application specific event
     * and creates the external representation.
    */
    class MessageTranslatorStrategy : public seda::StrategyDecorator {
    public:
        MessageTranslatorStrategy(const seda::Strategy::Ptr &decorated);
        virtual ~MessageTranslatorStrategy() {}

        virtual void perform(const seda::IEvent::Ptr&);
    private:
        XBE_DECLARE_LOGGER();
        TaskData parseTaskDescription(xbemsg::execute_t::task_type &);
    };
}

#endif // !XBE_MESSAGE_TRANSLATOR_STRATEGY_HPP


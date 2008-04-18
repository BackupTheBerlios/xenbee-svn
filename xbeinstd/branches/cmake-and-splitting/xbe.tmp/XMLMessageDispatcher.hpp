#ifndef XBE_XML_MESSAGE_DISPATCHER_HPP
#define XBE_XML_MESSAGE_DISPATCHER_HPP 1

#include <seda/StrategyDecorator.hpp>

#include <xbe/XMLMessageEvent.hpp>

namespace xbe {
    /**
       This class  is used to dispatch  received XML messages  to a finite
       state machine.

       Replace this class with your own one using this as a template.
    */
    class XMLMessageDispatcher : public seda::StrategyDecorator {
    public:
        XMLMessageDispatcher(const seda::Strategy::Ptr& s)
            : seda::StrategyDecorator(s->name()+".xml-fsm-gateway", s)
        {}
        virtual ~XMLMessageDispatcher() {}

        virtual void perform(const seda::IEvent::Ptr&) const;
    protected:
        virtual void dispatch(const xbemsg::message_t& msg) = 0;
    };
}

#endif // !XBE_XML_MESSAGE_DISPATCHER_HPP

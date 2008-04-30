#ifndef XBE_XML_MESSAGE_DISPATCHER_HPP
#define XBE_XML_MESSAGE_DISPATCHER_HPP 1

#include <seda/Strategy.hpp>

#include <xbe/XMLMessageEvent.hpp>

namespace xbe {
    /**
       This class  is used to dispatch  received XML messages  to a finite
       state machine.

       Replace this class with your own one using this as a template.
    */
    class XMLMessageDispatcher : public seda::Strategy {
    public:
        XMLMessageDispatcher()
            : seda::Strategy("xml-fsm-gateway")
        {}

        explicit
        XMLMessageDispatcher(const std::string& name)
            : seda::Strategy(name)
        {}
        virtual ~XMLMessageDispatcher() {}

        virtual void perform(const seda::IEvent::Ptr&) const;
    protected:
        virtual void dispatch(const xbemsg::message_t& msg) = 0;
    };
}

#endif // !XBE_XML_MESSAGE_DISPATCHER_HPP

#ifndef XBE_XML_MESSAGE_DISPATCHER_HPP
#define XBE_XML_MESSAGE_DISPATCHER_HPP 1

#include <xbe/common.hpp>
#include <xbe/XMLMessageEvent.hpp>

#include <seda/Strategy.hpp>

namespace xbe {
    /**
       This class  is used to dispatch  received XML messages  to a finite
       state machine or to whatever you like.

       Replace this class with your own one using this as a template.
    */
    class XMLMessageDispatcher : public seda::Strategy {
    public:
        explicit
        XMLMessageDispatcher(const std::string& name)
            : seda::Strategy(name),
              XBE_INIT_LOGGER(name)
        {}
        virtual ~XMLMessageDispatcher() {}

        virtual void perform(const seda::IEvent::Ptr&) const = 0;
    private:
        XBE_DECLARE_LOGGER();
    };
}

#endif // !XBE_XML_MESSAGE_DISPATCHER_HPP

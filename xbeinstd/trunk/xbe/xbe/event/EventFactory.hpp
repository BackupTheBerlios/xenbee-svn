#ifndef XBE_EVENT_FACTORY_HPP
#define XBE_EVENT_FACTORY_HPP 1

#include <mqs/Message.hpp>
#include <cms/CMSException.h>

#include <xbe/logging.hpp>
#include <seda/IEvent.hpp>
#include <seda/SystemEvent.hpp>

#include <xbe/XbeException.hpp>

namespace xbe {
    namespace event {
        class EventFactoryException : public XbeException {
            public:
                explicit
                    EventFactoryException(const std::string& reason)
                    : XbeException(reason) {};
        };
        class UnknownConversion : public EventFactoryException {
            public:
                explicit
                    UnknownConversion(const std::string& reason)
                    : EventFactoryException(reason) {};
        };

        class EventFactory {
            public:
                static const EventFactory& instance();
                ~EventFactory();

                seda::IEvent::Ptr newEvent(const mqs::Message&) const throw(UnknownConversion);
                seda::IEvent::Ptr newEvent(const cms::CMSException&) const;
                seda::IEvent::Ptr newEvent(const std::exception&) const;

                seda::SystemEvent::Ptr newErrorEvent(const std::string& msg, const std::string& additionalData="") const;
            private:
                EventFactory();

                XBE_DECLARE_LOGGER();
        };
    }
}

#endif // !XBE_EVENT_FACTORY_HPP

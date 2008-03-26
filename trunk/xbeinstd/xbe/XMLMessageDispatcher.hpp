#ifndef XBE_XML_MESSAGE_DISPATCHER_HPP
#define XBE_XML_MESSAGE_DISPATCHER_HPP 1

#include <seda/StrategyDecorator.hpp>

#include <xbe/XMLMessageEvent.hpp>

namespace xbe {
    /**
       Dispatches XML messages to a finite state machine FSM.
    */
    class XMLMessageDispatcher : public seda::StrategyDecorator {
    public:
        XMLMessageDispatcher(const seda::Strategy::Ptr& s, xbe::FSM& fsm)
            : seda::StrategyDecorator(s->name()+".xml-fsm-gateway", s),
              _fsm(fsm)
        {}
        virtual ~XMLMessageDispatcher() {}

        virtual void perform(const seda::IEvent::Ptr&) const;

    private:
        xbe::FSM& _fsm;
    };

    void XMLMessageDispatcher::perform(const seda::IEvent::Ptr& e) const {
        const XMLMessageEvent* xmlEvent(dynamic_cast<const XMLMessageEvent*>(e.get()));
        if (xmlEvent) {
            xbexsd::body_t& body(xmlEvent->message().body());
            
            if (body.error()) {
                _fsm.Error(xmlEvent);
            } else if (body.certifcate_req()) {
                _fsm.CertificateReq(xmlEvent);
            } else {
                LOG_ERROR("cannot dispatch message (unknown message type)");
            }
            
            seda::StrategyDecorator::perform(msgEvent);
        } else {
            LOG_WARN("throwing away non-XMLMessageEvent: " << e);
        }
    }
}

#endif // !XBE_XML_MESSAGE_DISPATCHER_HPP

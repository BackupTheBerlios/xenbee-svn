#include "MessageTranslatorStrategy.hpp"

#include "event/ObjectEvent.hpp"
#include "event/XbeInstdEvent.hpp"
#include "event/ExecuteAckEvent.hpp"
#include "event/ExecuteEvent.hpp"
#include "event/FailedAckEvent.hpp"
#include "event/FailedEvent.hpp"
#include "event/FinishedAckEvent.hpp"
#include "event/FinishedEvent.hpp"
#include "event/LifeSignEvent.hpp"
#include "event/ShutdownAckEvent.hpp"
#include "event/ShutdownEvent.hpp"
#include "event/StatusEvent.hpp"
#include "event/StatusReqEvent.hpp"
#include "event/TerminateAckEvent.hpp"
#include "event/TerminateEvent.hpp"

#include "xbe-msg.hpp"

#include <iostream>

using namespace xbe;
using namespace xbe::event;

MessageTranslatorStrategy::MessageTranslatorStrategy(const std::string& name,
        const seda::Strategy::Ptr& decorated)
: seda::StrategyDecorator(name, decorated),
    XBE_INIT_LOGGER(name)
{} 

void MessageTranslatorStrategy::perform(const seda::IEvent::Ptr& e) {
    if (xbe::event::ObjectEvent<xbemsg::message_t> *oe = (dynamic_cast<xbe::event::ObjectEvent<xbemsg::message_t>*>(e.get()))) {
        using namespace xercesc;

        // extract the body element and transform it into an internal
        // event
        std::auto_ptr<xbemsg::message_t> msg(oe->object());

        const std::string to(msg->header().to());
        const std::string from(msg->header().from());
        const std::string convID(msg->header().conversation_id());            

        if (msg->body().execute().present()) {
            XBE_LOG_INFO("translating execute");
            xbe::event::ExecuteEvent *evt(new xbe::event::ExecuteEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().terminate().present()) {
            XBE_LOG_INFO("translating terminate");
            xbe::event::TerminateEvent *evt(new xbe::event::TerminateEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().status_req().present()) {
            XBE_LOG_INFO("translating status-req");
            xbe::event::StatusReqEvent *evt(new xbe::event::StatusReqEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().shutdown().present()) {
            XBE_LOG_INFO("translating shutdown");
            xbe::event::ShutdownEvent *evt(new xbe::event::ShutdownEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().finished_ack().present()) {
            XBE_LOG_INFO("translating finished-ack");
            xbe::event::FinishedAckEvent *evt(new xbe::event::FinishedAckEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().failed_ack().present()) {
            XBE_LOG_INFO("translating failed-ack");
            xbe::event::FailedAckEvent *evt(new xbe::event::FailedAckEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().life_sign().present()) {
            XBE_LOG_INFO("translating life-sign");
            xbe::event::LifeSignEvent *evt(new xbe::event::LifeSignEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().execute_ack().present()) {
            XBE_LOG_INFO("translating execute-ack");
            xbe::event::ExecuteAckEvent *evt(new xbe::event::ExecuteAckEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().terminate_ack().present()) {
            XBE_LOG_INFO("translating terminate-ack");
            xbe::event::TerminateAckEvent *evt(new xbe::event::TerminateAckEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().shutdown_ack().present()) {
            XBE_LOG_INFO("translating shutdown-ack");
            xbe::event::ShutdownAckEvent *evt(new xbe::event::ShutdownAckEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().status().present()) {
            XBE_LOG_INFO("translating status");
            xbe::event::StatusEvent *evt(new xbe::event::StatusEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().finished().present()) {
            XBE_LOG_INFO("translating finished");
            xbe::event::FinishedEvent *evt(new xbe::event::FinishedEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else if (msg->body().failed().present()) {
            XBE_LOG_INFO("translating failed");
            xbe::event::FailedEvent *evt(new xbe::event::FailedEvent(to, from, convID));

            seda::StrategyDecorator::perform(seda::IEvent::Ptr(evt));
        } else {
            XBE_LOG_ERROR("got some unknown body element!");
        }
    } else if (xbe::event::XbeInstdEvent *xbeEvent = (dynamic_cast<xbe::event::XbeInstdEvent*>(e.get()))) {
        // got an internal event, transform it to xml
        if (xbe::event::ExecuteEvent *evt = dynamic_cast<xbe::event::ExecuteEvent*>(xbeEvent)) {
        } else if (xbe::event::TerminateEvent *evt = dynamic_cast<xbe::event::TerminateEvent*>(xbeEvent)) {
        } else if (xbe::event::StatusReqEvent *evt = dynamic_cast<xbe::event::StatusReqEvent*>(xbeEvent)) {
        } else if (xbe::event::ShutdownEvent *evt = dynamic_cast<xbe::event::ShutdownEvent*>(xbeEvent)) {
        } else if (xbe::event::FinishedAckEvent *evt = dynamic_cast<xbe::event::FinishedAckEvent*>(xbeEvent)) {
        } else if (xbe::event::FailedAckEvent *evt = dynamic_cast<xbe::event::FailedAckEvent*>(xbeEvent)) {
        } else if (xbe::event::LifeSignEvent *evt = dynamic_cast<xbe::event::LifeSignEvent*>(xbeEvent)) {
        } else if (xbe::event::ExecuteAckEvent *evt = dynamic_cast<xbe::event::ExecuteAckEvent*>(xbeEvent)) {
        } else if (xbe::event::TerminateAckEvent *evt = dynamic_cast<xbe::event::TerminateAckEvent*>(xbeEvent)) {
        } else if (xbe::event::ShutdownAckEvent *evt = dynamic_cast<xbe::event::ShutdownAckEvent*>(xbeEvent)) {
        } else if (xbe::event::StatusEvent *evt = dynamic_cast<xbe::event::StatusEvent*>(xbeEvent)) {
        } else if (xbe::event::FinishedEvent *evt = dynamic_cast<xbe::event::FinishedEvent*>(xbeEvent)) {
        } else if (xbe::event::FailedEvent *evt = dynamic_cast<xbe::event::FailedEvent*>(xbeEvent)) {
        } else {
        }
    } else {
        XBE_LOG_WARN("got some unknown event: " << e->str());
    }
}


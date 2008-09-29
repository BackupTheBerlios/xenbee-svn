#include <seda/SystemEvent.hpp>

#include "ChannelAdapterStrategy.hpp"
#include "MessageEvent.hpp"
#include "EventFactory.hpp"
#include "ChannelCommandEvent.hpp"

using namespace xbe;

ChannelAdapterStrategy::ChannelAdapterStrategy(const std::string& name,
                                               const seda::Strategy::Ptr& decorated,
                                               const mqs::Channel::Ptr& channel)
    : seda::StrategyDecorator(name, decorated),
      XBE_INIT_LOGGER(name),
      _channel(channel)
{
    _channel->setMessageListener(this);
}

ChannelAdapterStrategy::~ChannelAdapterStrategy() {}

void ChannelAdapterStrategy::onMessage(const cms::Message *m) {
    try {
        XBE_LOG_INFO("got new message from the network");
        StrategyDecorator::perform(EventFactory::instance().newEvent(m));
    } catch (const xbe::UnknownConversion& ex) {
        XBE_LOG_DEBUG("cms::Message could not be converted to Event: " << ex.what());
    } catch (const std::exception& ex) {
        XBE_LOG_WARN("message lost due to error during push: " << ex.what());
    } catch (...) {
        XBE_LOG_WARN("message lost due to error during push: unknown error");
    }
}

void ChannelAdapterStrategy::onException(const cms::CMSException& ex) {
    try {
        StrategyDecorator::perform(EventFactory::instance().newEvent(ex));
    } catch (...) {
        XBE_LOG_WARN("error event lost due to error during push");
    }
}

void ChannelAdapterStrategy::perform(const seda::IEvent::Ptr& e) const {
    XBE_LOG_DEBUG("handling event: " << e->str());
    // handle messages
    if (xbe::MessageEvent *msgEvent = dynamic_cast<xbe::MessageEvent*>(e.get())) {
        try {
            if (msgEvent->destination().isValid()) {
                XBE_LOG_DEBUG("sending message `"<< msgEvent->message() << "' to " << msgEvent->destination().str());
                _channel->send(msgEvent->message(), msgEvent->destination());
            } else {
                XBE_LOG_DEBUG("sending message `"<< msgEvent->message() << "'");
                _channel->send(msgEvent->message());
            }
        } catch(const cms::CMSException& ex) {
            StrategyDecorator::perform(EventFactory::instance().newEvent(ex));
        } catch(const std::exception& ex) {
            StrategyDecorator::perform(EventFactory::instance().newEvent(ex));
        } catch(...) {
            StrategyDecorator::perform(EventFactory::instance().newErrorEvent("unknown error during message sending"));
        }
    } else if (seda::SystemEvent *systemEvent = dynamic_cast<seda::SystemEvent*>(e.get())) {
        if (xbe::ChannelCommandEvent *channelCommand = dynamic_cast<xbe::ChannelCommandEvent*>(systemEvent)) {
            XBE_LOG_DEBUG("got command for channel: " << channelCommand->str());
            channelCommand->execute(_channel);
        } else {
            StrategyDecorator::perform(e);
        }
    } else {
        XBE_LOG_WARN("ignoring non-MessageEvent: " << e->str());
    }
}

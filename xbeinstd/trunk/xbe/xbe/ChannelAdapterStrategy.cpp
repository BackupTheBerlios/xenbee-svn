#include <seda/SystemEvent.hpp>
#include "event/MessageEvent.hpp"
#include "event/EventFactory.hpp"
#include "event/ChannelCommandEvent.hpp"

#include "ChannelAdapterStrategy.hpp"

using namespace xbe;
using namespace xbe::event;

ChannelAdapterStrategy::ChannelAdapterStrategy(const std::string& name,
                                               const seda::Strategy::Ptr& decorated,
                                               const mqs::Channel::Ptr& channel)
    : seda::StrategyDecorator(name, decorated),
      XBE_INIT_LOGGER(name),
      _channel(channel)
{
    _channel->setMessageListener(this);
    _channel->setExceptionListener(this);
}

ChannelAdapterStrategy::~ChannelAdapterStrategy() {}

void ChannelAdapterStrategy::onStageStart(const std::string &name) {
    _channel->start();
}

void ChannelAdapterStrategy::onStageStop(const std::string &name) {
    _channel->stop();
}

void ChannelAdapterStrategy::onMessage(const mqs::Message::Ptr &m) {
    try {
        XBE_LOG_INFO("got new message from the network");
        StrategyDecorator::perform(EventFactory::instance().newEvent(*m));
    } catch (const xbe::event::UnknownConversion& ex) {
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
        XBE_LOG_WARN("could not transform cms::exception to event: " << ex.getMessage());
    }
}

void ChannelAdapterStrategy::onException(const mqs::MQSException& ex) {
    try {
        StrategyDecorator::perform(EventFactory::instance().newEvent(ex));
    } catch (...) {
        XBE_LOG_WARN("could not transform cms::exception to event: " << ex.what());
    }
}

void ChannelAdapterStrategy::perform(const seda::IEvent::Ptr& e) {
    XBE_LOG_DEBUG("handling event: " << e->str());
    // handle messages
    if (xbe::event::MessageEvent *msgEvent = dynamic_cast<xbe::event::MessageEvent*>(e.get())) {
        try {
            if (msgEvent->destination().isValid() && msgEvent->source().isValid()) {
                XBE_LOG_DEBUG("sending message `"<< msgEvent->message() << "': " << msgEvent->source().str() << " -> " << msgEvent->destination().str());
                _channel->send(mqs::Message(msgEvent->message(), msgEvent->source(), msgEvent->destination()));
            } else {
                XBE_LOG_DEBUG("cannot send message, source or destination unknown!");
            }
        } catch(const cms::CMSException& ex) {
            StrategyDecorator::perform(EventFactory::instance().newEvent(ex));
        } catch(const std::exception& ex) {
            StrategyDecorator::perform(EventFactory::instance().newEvent(ex));
        } catch(...) {
            StrategyDecorator::perform(EventFactory::instance().newErrorEvent("unknown error during message sending"));
        }
    } else if (seda::SystemEvent *systemEvent = dynamic_cast<seda::SystemEvent*>(e.get())) {
        if (xbe::event::ChannelCommandEvent *channelCommand = dynamic_cast<xbe::event::ChannelCommandEvent*>(systemEvent)) {
            XBE_LOG_DEBUG("got command for channel: " << channelCommand->str());
            channelCommand->execute(_channel);
        } else {
            StrategyDecorator::perform(e);
        }
    } else {
        XBE_LOG_WARN("ignoring non-MessageEvent: " << e->str());
    }
}

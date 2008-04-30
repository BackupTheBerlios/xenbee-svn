#include "ChannelEventQueueAdapter.hpp"
#include "MessageEvent.hpp"
#include "EventFactory.hpp"

using namespace xbe;

ChannelEventQueueAdapter::ChannelEventQueueAdapter(const mqs::Channel::Ptr& channel, std::size_t maxQueueSize)
    : seda::EventQueue("channeladapter", maxQueueSize),
      _channel(channel) {
    _channel->setMessageListener(this);
}

ChannelEventQueueAdapter::~ChannelEventQueueAdapter() {}

void ChannelEventQueueAdapter::onMessage(const cms::Message *m) {
    try {
        EventQueue::push(EventFactory::instance().newEvent(m));
    } catch (const xbe::UnknownConversion& ex) {
        LOG_DEBUG("cms::Message could not be converted to Event: " << ex.what());
    } catch (const std::exception& ex) {
        LOG_WARN("message lost due to error during push: " << ex.what());
    } catch (...) {
        LOG_WARN("message lost due to error during push: unknown error");
    }
}

void ChannelEventQueueAdapter::onException(const cms::CMSException& ex) {
    try {
        EventQueue::push(EventFactory::instance().newEvent(ex));
    } catch (...) {
        LOG_WARN("error event lost due to error during push");
    }
}

void ChannelEventQueueAdapter::push(const seda::IEvent::Ptr& e) throw (seda::QueueFull) {
    xbe::MessageEvent *msgEvent(dynamic_cast<xbe::MessageEvent*>(e.get()));
    if (msgEvent) {
        try {
            if (msgEvent->destination().isValid()) {
                LOG_DEBUG("sending message `"<< msgEvent->message() << "' to " << msgEvent->destination().str());
                _channel->send(msgEvent->message(), msgEvent->destination());
            } else {
                LOG_DEBUG("sending message `"<< msgEvent->message() << "'");
                _channel->send(msgEvent->message());
            }
        } catch(const cms::CMSException& ex) {
            EventQueue::push(EventFactory::instance().newEvent(ex));
        } catch(const std::exception& ex) {
            EventQueue::push(EventFactory::instance().newEvent(ex));
        } catch(...) {
            EventQueue::push(EventFactory::instance().newErrorEvent("unknown error during message sending"));
        }
    } else {
        // system events go to the real queue
        seda::SystemEvent *systemEvent(dynamic_cast<seda::SystemEvent*>(e.get()));
        if (systemEvent) {
            EventQueue::push(e);
        } else {
            LOG_INFO("ignoring non-MessageEvent:" << e->str());
        }
    }
}

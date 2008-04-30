#ifndef XBE_CHANNEL_ADAPTER_STRATEGY_HPP
#define XBE_CHANNEL_ADAPTER_STRATEGY_HPP 1

#include <cms/MessageListener.h>
#include <cms/ExceptionListener.h>
#include <activemq/concurrent/Lock.h>
#include <activemq/concurrent/Mutex.h>

#include <mqs/Channel.hpp>

#include <seda/constants.hpp>
#include <seda/StrategyDecorator.hpp>
#include <seda/IEvent.hpp>
#include <seda/SystemEvent.hpp>

#include <xbe/common.hpp>

namespace xbe {
    class ChannelAdapterStrategy : public seda::StrategyDecorator,
                                   public cms::MessageListener,
                                   public cms::ExceptionListener {

    public:
        ChannelAdapterStrategy(const std::string& name,
                               const seda::Strategy::Ptr& decorated,
                               const mqs::Channel::Ptr& channel);
        ~ChannelAdapterStrategy();

        /**
         * Handles events  that are  either destined to  be sent  over the
         * channel or to control the channel itself.
         *
         * MessageEvents are sent over the channel.
         * ControlEvents are used to control the channel:
         *     Connect(BrokerURI)
         *         let the channel connect to the given broker
         *     Disconnect
         *         disconnect the channel
         *     Reconnect
         *         let the channel connect to the last broker
         *
         * Are control flow messages required?
         *     Pause/Resume etc.
         */
        virtual void perform(const seda::IEvent::Ptr&) const;

        /***********************************
         *  MessageListener interface
         ***********************************/
        void onMessage(const cms::Message* m);

        /***********************************
         *  ExceptionListener interface
         ***********************************/
        void onException(const cms::CMSException& ex);
    private:
        mqs::Channel::Ptr _channel;
    };
}

#endif // !XBE_CHANNEL_ADAPTER_STRATEGY_HPP

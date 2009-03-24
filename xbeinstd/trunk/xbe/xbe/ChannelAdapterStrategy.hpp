#ifndef XBE_CHANNEL_ADAPTER_STRATEGY_HPP
#define XBE_CHANNEL_ADAPTER_STRATEGY_HPP 1

#include <mqs/MessageListener.hpp>
#include <mqs/ExceptionListener.hpp>

#include <mqs/Channel.hpp>

#include <seda/constants.hpp>
#include <seda/StrategyDecorator.hpp>
#include <seda/IEvent.hpp>
#include <seda/SystemEvent.hpp>

#include <xbe/common.hpp>

namespace xbe {
    class ChannelAdapterStrategy : public seda::StrategyDecorator,
                                   public mqs::MessageListener,
                                   public mqs::ExceptionListener {

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
        virtual void perform(const seda::IEvent::Ptr&);

        void onStageStart(const std::string &name);
        void onStageStop(const std::string &name);

        /***********************************
         *  MessageListener interface
         ***********************************/
        void onMessage(const mqs::Message::Ptr &m);

        /***********************************
         *  ExceptionListener interface
         ***********************************/
        void onException(const cms::CMSException& ex);
        void onException(const mqs::MQSException& ex);
    private:
        XBE_DECLARE_LOGGER();
        mqs::Channel::Ptr _channel;
    };
}

#endif // !XBE_CHANNEL_ADAPTER_STRATEGY_HPP

#ifndef XBE_CHANNEL_EVENT_QUEUE_ADAPTER_HPP
#define XBE_CHANNEL_EVENT_QUEUE_ADAPTER_HPP 1

#include <cms/MessageListener.h>
#include <cms/ExceptionListener.h>
#include <activemq/concurrent/Lock.h>
#include <activemq/concurrent/Mutex.h>

#include <mqs/Channel.hpp>

#include <seda/constants.hpp>
#include <seda/IEvent.hpp>
#include <seda/EventQueue.hpp>

#include <xbe/common.hpp>

namespace xbe {
  class ChannelEventQueueAdapter : public seda::EventQueue,
				   public cms::MessageListener,
				   public cms::ExceptionListener
  {
  public:
    ChannelEventQueueAdapter(const mqs::Channel::Ptr& channel, std::size_t maxQueueSize=seda::SEDA_MAX_QUEUE_SIZE);
    ~ChannelEventQueueAdapter();

    /***********************************
     *  overloaded EventQueue methods
     ***********************************/

    void push(const seda::IEvent::Ptr& e) throw (seda::QueueFull);


    /***********************************
     *  MessageListener interface
     ***********************************/
    void onMessage(const cms::Message* m);

    /***********************************
     *  ExceptionListener interface
     ***********************************/
    void onException(const cms::CMSException& ex);
    
  private:
    XBE_DECLARE_LOGGER();
    mqs::Channel::Ptr _channel;
  };
}

#endif // !XBE_CHANNEL_EVENT_QUEUE_ADAPTER_HPP

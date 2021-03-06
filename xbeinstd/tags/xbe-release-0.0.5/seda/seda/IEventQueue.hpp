#ifndef SEDA_IEVENT_QUEUE_HPP
#define SEDA_IEVENT_QUEUE_HPP 1

#include <tr1/memory>

#include <seda/IEvent.hpp>
#include <seda/SedaException.hpp>

namespace seda {
  class QueueEmpty : public SedaException {
  public:
    QueueEmpty() : SedaException("queue is empty") {}
  };

  class QueueFull : public SedaException {
  public:
    QueueFull() : SedaException("queue is full") {}
  };

  class IEventQueue {
  public:
    typedef std::tr1::shared_ptr<IEventQueue> Ptr;
    
    virtual ~IEventQueue() {}

    virtual IEvent::Ptr pop() throw (QueueEmpty) = 0;
    virtual IEvent::Ptr pop(unsigned long millis) throw (QueueEmpty) = 0;
    
    virtual void push(const IEvent::Ptr& e) throw (QueueFull) = 0;
    
    virtual void clear() = 0;

    virtual std::size_t size() const = 0;
    virtual bool empty() const = 0;
    virtual std::size_t maxQueueSize() const = 0;
    virtual void maxQueueSize(const std::size_t& max) = 0;

    virtual void waitUntilEmpty() const = 0;
    virtual void waitUntilEmpty(unsigned long millis) const = 0;
    virtual void waitUntilNotEmpty() const = 0;
    virtual void waitUntilNotEmpty(unsigned long millis) const = 0;
    virtual void notify() = 0;
    virtual void notifyAll() = 0;
  protected:
    IEventQueue() {}
  };
}

#endif // !SEDA_IEVENT_QUEUE_HPP

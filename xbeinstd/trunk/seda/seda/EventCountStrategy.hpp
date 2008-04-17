#ifndef SEDA_EVENT_COUNT_STRATEGY_HPP
#define SEDA_EVENT_COUNT_STRATEGY_HPP 1

#include <activemq/util/Date.h>
#include <activemq/concurrent/Mutex.h>
#include <activemq/concurrent/Lock.h>

#include <seda/StrategyDecorator.hpp>

namespace seda {
  class EventCountStrategy : public StrategyDecorator {
  public:
    typedef std::tr1::shared_ptr<EventCountStrategy> Ptr;
    
    explicit
    EventCountStrategy(const Strategy::Ptr& s)
      : StrategyDecorator(s->name()+".count", s),
	_count(0)
    {}
    ~EventCountStrategy() {}

    void perform(const IEvent::Ptr& e) const {
      inc();
      StrategyDecorator::perform(e);
    }

    std::size_t count() const { return _count; }
    void reset() {
      activemq::concurrent::Lock lock(&_mtx);
      _count=0;
    }
    void inc() const {
      activemq::concurrent::Lock lock(&_mtx);
      _count++;
      _mtx.notifyAll();
    }
    void wait(std::size_t targetValue, unsigned long millis=WAIT_INFINITE) const {
      activemq::concurrent::Lock lock(&_mtx);
      using namespace activemq::util;
      unsigned long long now(Date::getCurrentTimeMilliseconds());
      while (count() < targetValue) {
	_mtx.wait(millis);
	if (millis != WAIT_INFINITE &&
	    (Date::getCurrentTimeMilliseconds() - now) > millis)
	  break;
      }
    }
    void waitNoneZero(unsigned long millis=WAIT_INFINITE) const {
      activemq::concurrent::Lock lock(&_mtx);
      using namespace activemq::util;
      unsigned long long now(Date::getCurrentTimeMilliseconds());
      while (count() == 0) {
	_mtx.wait(millis);
	if (millis != WAIT_INFINITE &&
	    (Date::getCurrentTimeMilliseconds() - now) > millis)
	  break;
      }
    }
  private:
    mutable std::size_t _count;
    mutable activemq::concurrent::Mutex _mtx;
  };
}

#endif // !SEDA_EVENT_COUNT_STRATEGY_HPP

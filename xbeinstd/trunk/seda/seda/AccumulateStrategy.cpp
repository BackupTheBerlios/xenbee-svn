#include "IEvent.hpp"
#include "IEventQueue.hpp"
#include "AccumulateStrategy.hpp"

namespace seda {
  void AccumulateStrategy::perform(const IEvent::Ptr& e) const {
    //Note: this is not threadsafe! 
    const_cast<AccumulateStrategy*>(this)->_accumulator.push_back(e);
    StrategyDecorator::perform(e);
  }
}

#include "IEvent.hpp"
#include "IEventQueue.hpp"
#include "AccumulateStrategy.hpp"

namespace seda {
    void AccumulateStrategy::perform(const IEvent::Ptr& e) {
        {
            boost::unique_lock<boost::recursive_mutex> lock(_mtx);
            _accumulator.push_back(e);
        }
        StrategyDecorator::perform(e);
    }
}

#include "IEvent.hpp"
#include "IEventQueue.hpp"
#include "CoutStrategy.hpp"

#include <activemq/concurrent/Thread.h>

namespace seda {
  void CoutStrategy::perform(const IEvent::Ptr& e) const {
    _os << e->str() << std::endl;
    activemq::concurrent::Thread::sleep(20);
  }
}

#include "IEvent.hpp"
#include "IEventQueue.hpp"
#include "ForwardStrategy.hpp"

namespace seda {
  void ForwardStrategy::perform(const IEvent::Ptr& e) const {
    LOG_DEBUG("forwarding event to stage `" << _next->name() << "'");
    _next->send(e);
  }
}

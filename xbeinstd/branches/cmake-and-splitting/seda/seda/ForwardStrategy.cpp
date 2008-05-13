#include "ForwardStrategy.hpp"

#include "IEvent.hpp"
#include "IEventQueue.hpp"
#include "StageRegistry.hpp"

namespace seda {
  void ForwardStrategy::perform(const IEvent::Ptr& e) const {
      const Stage::Ptr& nextStage(StageRegistry::instance().lookup(_next));
      if (nextStage) {
          SEDA_LOG_DEBUG("forwarding event to stage `" << nextStage->name() << "'");
          nextStage->send(e);
      } else {
          SEDA_LOG_WARN("nothing to forward to!");
      }
  }
}

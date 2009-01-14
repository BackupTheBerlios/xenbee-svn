#include "ForwardStrategy.hpp"

#include "IEvent.hpp"
#include "IEventQueue.hpp"
#include "StageRegistry.hpp"
#include <iostream>

namespace seda {
  void ForwardStrategy::perform(const IEvent::Ptr& e) {
      const Stage::Ptr& nextStage(StageRegistry::instance().lookup(_next));
      if (nextStage) {
        std::cout << "nasty line here." << std::endl;
        std::cout << "talking to: "<< _next << std::endl;
          //SEDA_LOG_WARN("forwarding event to stage `" << nextStage->name() << "'");
        std::cout << "after log." << std::endl;
          nextStage->send(e);
        std::cout << "after send." << std::endl;
      } else {
          SEDA_LOG_WARN("nothing to forward to!");
      }
  }
}

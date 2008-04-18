#ifndef SEDA_DISCARD_STRATEGY_HPP
#define SEDA_DISCARD_STRATEGY_HPP 1

#include <iostream>

#include <seda/Strategy.hpp>

namespace seda {
  class DiscardStrategy : public Strategy {
  public:
    DiscardStrategy() : Strategy("discard") {}
    ~DiscardStrategy() {}

    void perform(const IEvent::Ptr&) const { }
  };
}

#endif // !SEDA_DISCARD_STRATEGY_HPP
#ifndef SEDA_FORWARD_STRATEGY_HPP
#define SEDA_FORWARD_STRATEGY_HPP 1

#include <seda/Strategy.hpp>
#include <seda/Stage.hpp>

namespace seda {
  class ForwardStrategy : public Strategy {
  public:
    ForwardStrategy(const Stage::Ptr& next)
      : Strategy("fwd-to-"+next->name()), _next(next) {}
    ForwardStrategy(const std::string& name, const Stage::Ptr& next)
      : Strategy(name), _next(next) {}
    virtual ~ForwardStrategy() {}

    virtual void perform(const IEvent::Ptr&) const;

  private:
    Stage::Ptr _next;
  };
}

#endif // !SEDA_FORWARD_STRATEGY_HPP

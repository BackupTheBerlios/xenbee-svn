#ifndef SEDA_ACCUMULATESTRATEGY_HPP
#define SEDA_ACCUMULATESTRATEGY_HPP 1

#include <seda/StrategyDecorator.hpp>
#include <list>


namespace seda {
  /* Accumulates the events sent to this StrategyDecorator.
   * NOTE: This is not threadsafe at the moment.
   */
  class AccumulateStrategy : public StrategyDecorator {
    public:
      typedef std::list<IEvent::Ptr>::iterator iterator_type;
      typedef std::tr1::shared_ptr<AccumulateStrategy> Ptr;
      explicit AccumulateStrategy(const Strategy::Ptr& s)
                : StrategyDecorator(s->name()+".accumulate", s),
        _accumulator() {}

      ~AccumulateStrategy() {}
      void perform(const IEvent::Ptr&) const;
      iterator_type getIEventIteratorBegin() { return _accumulator.begin(); }
      iterator_type getIEventIteratorEnd() { return _accumulator.end(); }
    private:
      std::list<IEvent::Ptr> _accumulator;
  };
}

#endif /* SEDA_ACCUMULATESTRATEGY_HPP */

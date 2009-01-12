#ifndef SEDA_ACCUMULATESTRATEGY_HPP
#define SEDA_ACCUMULATESTRATEGY_HPP 1

#include <seda/StrategyDecorator.hpp>
#include <boost/thread.hpp>
#include <list>


namespace seda {
  /* Accumulates the events sent to this StrategyDecorator.
   */
  class AccumulateStrategy : public StrategyDecorator {
    public:
      typedef std::list<IEvent::Ptr>::iterator iterator_type;
      typedef std::list<IEvent::Ptr>::const_iterator const_iterator;
      typedef std::tr1::shared_ptr<AccumulateStrategy> Ptr;
      explicit AccumulateStrategy(const Strategy::Ptr& s)
                : StrategyDecorator(s->name()+".accumulate", s),
        _accumulator() {}

      ~AccumulateStrategy() {}
      void perform(const IEvent::Ptr&);
      iterator_type getIEventIteratorBegin() { return _accumulator.begin(); }
      iterator_type getIEventIteratorEnd() { return _accumulator.end(); }
      std::size_t size() { return _accumulator.size(); }
      void clear() { _accumulator.clear(); }
      bool empty() { return (_accumulator.size() == 0); }
      const_iterator begin() const { return _accumulator.begin(); }
      const_iterator end() const { return _accumulator.end(); }
    private:
      std::list<IEvent::Ptr> _accumulator;
      boost::recursive_mutex _mtx;
  };
}

#endif /* SEDA_ACCUMULATESTRATEGY_HPP */

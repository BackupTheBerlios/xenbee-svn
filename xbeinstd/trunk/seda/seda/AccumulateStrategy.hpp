#ifndef SEDA_ACCUMULATESTRATEGY_HPP
#define SEDA_ACCUMULATESTRATEGY_HPP 1

#include <seda/Strategy.hpp>
#include <list>


namespace seda {
  class AccumulateStrategy : public Strategy {
    public:
      typedef std::list<IEvent::Ptr>::iterator iterator_type;
      typedef std::tr1::shared_ptr<AccumulateStrategy> Ptr;
      AccumulateStrategy(const std::string& name) : 
        Strategy(name), 
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

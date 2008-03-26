#ifndef SEDA_STRATEGY_HPP
#define SEDA_STRATEGY_HPP 1

#include <tr1/memory>
#include <seda/logging.hpp>

#include <seda/IEvent.hpp>

namespace seda {
  class IEvent;
  
  class Strategy {
  public:
    typedef std::tr1::shared_ptr<Strategy> Ptr;
    
    virtual ~Strategy() {}
    virtual void perform(const IEvent::Ptr&) const = 0;
    const std::string& name() const { return _name; }
  protected:
    explicit
    Strategy(const std::string& name)
      : INIT_LOGGER("seda.strategy."+name), _name(name)
    {}
    DECLARE_LOGGER();
  private:
    std::string _name;
  };
}

#endif // ! SEDA_STRATEGY_HPP

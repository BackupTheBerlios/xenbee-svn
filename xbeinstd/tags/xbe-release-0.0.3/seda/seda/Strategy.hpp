#ifndef SEDA_STRATEGY_HPP
#define SEDA_STRATEGY_HPP 1

#include <tr1/memory>
#include <seda/common.hpp>

#include <seda/IEvent.hpp>

namespace seda {
    class IEvent;
  
    class Strategy {
    public:
        typedef std::tr1::shared_ptr<Strategy> Ptr;
    
        virtual ~Strategy() {}
        virtual void perform(const IEvent::Ptr&) const = 0;
        const std::string& name() const { return _name; }

        /* TODO:  introduce a notation  for maximum  number of  threads this
           strategy supports.  It may be that particular  strategies must be
           executed sequentially. Can also be solved by acquiring a mutex from
           withing the perform method. */
    protected:
        explicit
        Strategy(const std::string& name) 
            : SEDA_INIT_LOGGER(name), _name(name)
        {}
        SEDA_DECLARE_LOGGER();
    private:
        std::string _name;
    };
}

#endif // ! SEDA_STRATEGY_HPP

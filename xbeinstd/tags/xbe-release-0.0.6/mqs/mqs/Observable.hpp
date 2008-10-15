#ifndef MQS_OBSERVABLE_HPP
#define MQS_OBSERVABLE_HPP 1

#include <mqs/Observer.hpp>
#include <list>

namespace mqs {
    class Observable {
    public:        
        void attach(Observer *observer);
        void detach(Observer *observer);
        void notify();
    private:
        std::list<Observer*> _observers;
    };
}

#endif // ! MQS_OBSERVABLE_HPP

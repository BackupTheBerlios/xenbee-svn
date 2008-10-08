#ifndef MQS_OBSERVER_HPP
#define MQS_OBSERVER_HPP 1

namespace mqs {
    class Observer {
    public:
        virtual void update() = 0;
    };
}

#endif // ! MQS_OBSERVER_HPP

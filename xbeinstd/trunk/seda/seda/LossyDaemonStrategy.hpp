#ifndef SEDA_LOSSY_DAEMON_STRATEGY_HPP
#define SEDA_LOSSY_DAEMON_STRATEGY_HPP 1

#include <iostream>

#include <seda/StrategyDecorator.hpp>

namespace seda {
    class LossyDaemonStrategy : public StrategyDecorator {
        public:
            explicit
            LossyDaemonStrategy(const Strategy::Ptr &s, double probability=0.1, unsigned int seed=1);
            ~LossyDaemonStrategy() {}

            void perform(const IEvent::Ptr&);
        private:
            double probability_;
            unsigned int seed_;
    };
}

#endif // !SEDA_LOSSY_DAEMON_STRATEGY_HPP

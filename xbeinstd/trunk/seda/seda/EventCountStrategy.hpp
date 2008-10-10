#ifndef SEDA_EVENT_COUNT_STRATEGY_HPP
#define SEDA_EVENT_COUNT_STRATEGY_HPP 1

#include <seda/util.hpp>
#include <seda/Mutex.hpp>
#include <seda/Condition.hpp>
#include <seda/Lock.hpp>

#include <seda/StrategyDecorator.hpp>

namespace seda {
    class EventCountStrategy : public StrategyDecorator {
        public:
            typedef std::tr1::shared_ptr<EventCountStrategy> Ptr;

            explicit
                EventCountStrategy(const Strategy::Ptr& s)
                : StrategyDecorator(s->name()+".count", s),
                _count(0) {}

            ~EventCountStrategy() {}

            void perform(const IEvent::Ptr& e) const {
                inc();
                StrategyDecorator::perform(e);
            }

            std::size_t count() const { return _count; }
            void reset() {
                seda::Lock lock(_mtx);
                _count=0;
            }
            void inc() const {
                seda::Lock lock(_mtx);
                _count++;
                _cond.notifyAll();
            }
            void wait(std::size_t targetValue, unsigned long millis=WAIT_INFINITE) const {
                seda::Lock lock(_mtx);
                unsigned long long now(seda::getCurrentTimeMilliseconds());
                while (count() < targetValue) {
                    _cond.wait(_mtx, millis);
                    if (millis != WAIT_INFINITE &&
                            (seda::getCurrentTimeMilliseconds() - now) > millis)
                        break;
                }
            }

            void waitNoneZero(unsigned long millis=WAIT_INFINITE) const {
                seda::Lock lock(_mtx);
                unsigned long long now(seda::getCurrentTimeMilliseconds());
                while (count() == 0) {
                    _cond.wait(_mtx, millis);
                    if (millis != WAIT_INFINITE &&
                            (seda::getCurrentTimeMilliseconds() - now) > millis)
                        break;
                }
            }
        private:
            mutable std::size_t _count;
            mutable seda::Mutex _mtx;
            mutable seda::Condition _cond;
    };
}

#endif // !SEDA_EVENT_COUNT_STRATEGY_HPP

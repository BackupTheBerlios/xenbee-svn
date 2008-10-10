#ifndef SEDA_SEMAPHORE_HPP
#define SEDA_SEMAPHORE_HPP 1

#include <seda/Condition.hpp>

namespace seda {
    class Semaphore {
        public:
            explicit
            Semaphore(unsigned int initialValue=1) : _value(initialValue) { }

            ~Semaphore() { }

            void P() {
                seda::Lock lock(_cond);
                while (_value == 0) {
                    _cond.wait();
                }
                _value--;
            }

            void V() {
                seda::Lock lock(_cond);
                _value++;
                _cond.notify();
            }

        private:
            unsigned int _value;
            seda::Condition _cond;
    };
}

#endif

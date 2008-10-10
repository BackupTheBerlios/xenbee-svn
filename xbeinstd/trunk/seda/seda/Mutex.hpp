#ifndef SEDA_MUTEX_HPP
#define SEDA_MUTEX_HPP 1

#include <pthread.h>
#include <assert.h>
#include <seda/Synchronizable.hpp>

namespace seda {
    class Mutex : public seda::Synchronizable {
        friend class Condition;

        public:
            Mutex() {
                pthread_mutex_init(&_impl, NULL);
            }

            ~Mutex() {
                int ret = pthread_mutex_destroy(&_impl);
                assert(ret == 0);
            }

            void acquire() {
                pthread_mutex_lock(&_impl);
            }

            void release() {
                pthread_mutex_unlock(&_impl);
            }
        private:
            pthread_mutex_t _impl;
    };
}

#endif

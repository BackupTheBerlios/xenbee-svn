#ifndef SEDA_CONDITION_HPP
#define SEDA_CONDITION_HPP 1

#include <seda/Synchronizable.hpp>
#include <seda/Mutex.hpp>
#include <sys/time.h>
#include <time.h>
#include <assert.h>
#include <pthread.h>

namespace seda {
    class Condition {
        public:
            Condition() {
                pthread_cond_init(&_cond, NULL);
            }

            ~Condition() {
                int ret = pthread_cond_destroy(&_cond);
                assert(ret == 0);
            }

            int wait(Mutex &mtx) {
                return pthread_cond_wait(&_cond,  &mtx._impl);
            }

            int wait(Mutex &mtx, unsigned long long ms) {
                struct timeval now;
                struct timespec timeout;
                gettimeofday(&now, NULL);
                unsigned long sec(ms / 1000);
                unsigned long rest(ms - (sec*1000));
                timeout.tv_sec = now.tv_sec + sec;
                timeout.tv_nsec = (now.tv_usec + rest) * 1000;
                return pthread_cond_timedwait(&_cond, &mtx._impl, &timeout);
            }

            void notify() {
                pthread_cond_signal(&_cond);
            }
            void notifyAll() {
                pthread_cond_broadcast(&_cond);
            }
        private:
            pthread_cond_t  _cond;
    };
}

#endif

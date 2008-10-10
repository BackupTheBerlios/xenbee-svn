#ifndef SEDA_THREAD_HPP
#define SEDA_THREAD_HPP 1

#include <pthread.h>
#include <string>

namespace seda {
    class Thread {
        public:
            explicit
                Thread() : _thread(0) {}
            ~Thread() {}

            void start();
            void join();
            int id();

            static int getId();
            static void sleep(unsigned long long ms);

            virtual void run() { }
        private:
            pthread_t _thread;
    };
}

#endif

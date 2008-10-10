#include "Thread.hpp"
#include "Mutex.hpp"
#include "Condition.hpp"

#include <stdexcept>
#include <assert.h>

using namespace seda;

static void * seda_thread_entry_func(void * arg) {
    seda::Thread *t = (seda::Thread*)(arg);
    t->run();
    return 0;
}

void Thread::start() {
    if (!_thread) {
        pthread_create(&_thread, NULL, seda_thread_entry_func, this);
    } else {
        assert(false);
    }
}

void Thread::join() {
    if (pthread_join(_thread, NULL) != 0) {
        throw std::runtime_error("thread-join failed!");
    }
}

int Thread::id() {
    return (int)_thread;
}

int Thread::getId() {
    return (int)pthread_self();
}

void Thread::sleep(unsigned long long ms) {
    seda::Mutex mtx;
    seda::Condition cond;
    mtx.acquire(); cond.wait(mtx, ms); mtx.release();
}

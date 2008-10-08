#ifndef MQS_MUTEX_HPP
#define MQS_MUTEX_HPP 1

#ifdef USE_ACTIVE_MQ_2_2_1
#include <decaf/util/concurrent/Synchronizable.h>
#include <decaf/util/concurrent/Mutex.h>
#include <decaf/util/concurrent/CountDownLatch.h>
#include <decaf/util/concurrent/Lock.h>
#define MQS_CONCURRENT_NS decaf::util::concurrent
#else
#include <activemq/concurrent/Synchronizable.h>
#include <activemq/concurrent/Mutex.h>
#include <activemq/concurrent/CountDownLatch.h>
#include <activemq/concurrent/Lock.h>
#define MQS_CONCURRENT_NS activemq::concurrent
#endif

namespace mqs {
    typedef MQS_CONCURRENT_NS::Mutex Mutex;
    typedef MQS_CONCURRENT_NS::Synchronizable Synchronizable;
    typedef MQS_CONCURRENT_NS::CountDownLatch Semaphore;
    typedef MQS_CONCURRENT_NS::Lock Lock;
}

#undef MQS_CONCURRENT_NS

#endif

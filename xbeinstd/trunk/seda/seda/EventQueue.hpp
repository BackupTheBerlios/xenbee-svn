#ifndef SEDA_EVENT_QUEUE_HPP
#define SEDA_EVENT_QUEUE_HPP 1

#include <list>
#include <tr1/memory>
#include <activemq/util/Date.h>
#include <activemq/concurrent/Mutex.h>
#include <activemq/concurrent/Lock.h>

#include <seda/common.hpp>
#include <seda/constants.hpp>
#include <seda/IEventQueue.hpp>
#include <seda/IEvent.hpp>

namespace seda {
    class EventQueue : public IEventQueue {
        public:
            typedef std::tr1::shared_ptr< EventQueue > Ptr;

            explicit
                EventQueue(const std::string& name, std::size_t maxQueueSize=SEDA_MAX_QUEUE_SIZE)
                : SEDA_INIT_LOGGER("seda.queue."+name),
                _name(name),
                _maxQueueSize(maxQueueSize) {}
            virtual ~EventQueue() {}

            const std::string& name() { return _name; }

            virtual IEvent::Ptr pop() throw(QueueEmpty) {
                return pop(WAIT_INFINITE);
            }

            virtual IEvent::Ptr pop(unsigned long millis) throw(QueueEmpty) {
                activemq::concurrent::Lock lock(&_mtx);
                using activemq::util::Date;
                unsigned long long now(Date::getCurrentTimeMilliseconds());
                while (empty()) {
                    _mtx.wait(millis);
                    if (millis != WAIT_INFINITE &&
                            (Date::getCurrentTimeMilliseconds() - now) > millis)
                        break;
                }
                if (empty()) {
                    activemq::concurrent::Lock emptyCondLock(&_emptyCond);
                    _emptyCond.notifyAll();
                    throw QueueEmpty();
                } else {
                    IEvent::Ptr e = _list.front();
                    _list.pop_front();
                    if (empty()) {
                        activemq::concurrent::Lock emptyCondLock(&_emptyCond);
                        _emptyCond.notifyAll();
                    } else {
                        activemq::concurrent::Lock notEmptyCondLock(&_notEmptyCond);
                        _notEmptyCond.notifyAll();
                    }
                    return e;
                }
            }

            virtual void push(const IEvent::Ptr& e) throw(QueueFull) {
                {
                    activemq::concurrent::Lock lock(&_mtx);
                    if (size() >= _maxQueueSize) {
                        throw QueueFull();
                    } else {
                        _list.push_back(e);
                        _mtx.notify();
                    }
                }

                activemq::concurrent::Lock notEmptyCondLock(&_notEmptyCond);
                _notEmptyCond.notifyAll();
            }

            virtual void waitUntilEmpty() const {
                waitUntilEmpty(WAIT_INFINITE);
            }

            virtual void waitUntilEmpty(unsigned long millis) const {
                activemq::concurrent::Lock lock(&_emptyCond);
                using namespace activemq::util;
                unsigned long long now(Date::getCurrentTimeMilliseconds());
                while (!empty()) {
                    _emptyCond.wait(millis);
                    if (millis != WAIT_INFINITE &&
                            (Date::getCurrentTimeMilliseconds() - now) > millis)
                        break;
                }
            }

            virtual void waitUntilNotEmpty() const {
                waitUntilNotEmpty(WAIT_INFINITE);
            }

            virtual void waitUntilNotEmpty(unsigned long millis) const {
                activemq::concurrent::Lock lock(&_notEmptyCond);
                using namespace activemq::util;
                unsigned long long now(Date::getCurrentTimeMilliseconds());
                while (empty()) {
                    _notEmptyCond.wait(millis);
                    if (millis != WAIT_INFINITE &&
                            (Date::getCurrentTimeMilliseconds() - now) > millis)
                        break;
                }
            }

            /**
              Removes all elements from the queue.

              Warning: elements will be deleted!
            */
            virtual void clear() {
                activemq::concurrent::Lock lock(&_mtx);
                while (!empty()) {
                    IEvent::Ptr e = _list.front();
                    _list.pop_front();
                }
            }

            virtual void notify() {
                activemq::concurrent::Lock lock(&_mtx);
                _mtx.notify();
            }
            virtual void notifyAll() {
                activemq::concurrent::Lock lock(&_mtx);
                _mtx.notifyAll();
            }
            virtual std::size_t size() const { return _list.size(); }
            bool empty() const { return _list.empty(); }

            std::size_t maxQueueSize() const { return _maxQueueSize; }
            void maxQueueSize(const std::size_t& max) { _maxQueueSize = max; }
        protected:
            SEDA_DECLARE_LOGGER();
            mutable activemq::concurrent::Mutex _mtx;
            mutable activemq::concurrent::Mutex _emptyCond;
            mutable activemq::concurrent::Mutex _notEmptyCond;

            std::list< IEvent::Ptr > _list;
        private:
            std::string _name;
            std::size_t _maxQueueSize;
    };
}

#endif

#ifndef SEDA_EVENT_QUEUE_HPP
#define SEDA_EVENT_QUEUE_HPP 1

#include <list>
#include <tr1/memory>

#include <seda/util.hpp>
#include <seda/Lock.hpp>
#include <seda/Mutex.hpp>
#include <seda/Condition.hpp>

#include <seda/common.hpp>
#include <seda/constants.hpp>
#include <seda/IEventQueue.hpp>
#include <seda/IEvent.hpp>

#define WAIT_INFINITE 0xFFFFffff

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
                seda::Lock lock(_mtx);
                unsigned long long now(seda::getCurrentTimeMilliseconds());
                while (empty()) {
                    _notEmptyCond.wait(_mtx, millis);
                    if (millis != WAIT_INFINITE && (seda::getCurrentTimeMilliseconds() - now) > millis)
                        break;
                }
                if (empty()) {
                    _emptyCond.notifyAll();
                    throw QueueEmpty();
                } else {
                    IEvent::Ptr e = _list.front();
                    _list.pop_front();
                    if (empty()) {
                        _emptyCond.notifyAll();
                    } else {
                        _notEmptyCond.notifyAll();
                    }
                    return e;
                }
            }

            virtual void push(const IEvent::Ptr& e) throw(QueueFull) {
                seda::Lock lock(_mtx);
                if (size() >= _maxQueueSize) {
                    throw QueueFull();
                } else {
                    _list.push_back(e);
                    _notEmptyCond.notify();
                }
            }

            virtual void waitUntilEmpty() const {
                waitUntilEmpty(WAIT_INFINITE);
            }

            virtual void waitUntilEmpty(unsigned long millis) const {
                seda::Lock lock(_mtx);
                unsigned long long now(seda::getCurrentTimeMilliseconds());
                while (!empty()) {
                    _emptyCond.wait(_mtx, millis);
                    if (millis != WAIT_INFINITE &&
                            (seda::getCurrentTimeMilliseconds() - now) > millis)
                        break;
                }
            }

            virtual void waitUntilNotEmpty() const {
                waitUntilNotEmpty(WAIT_INFINITE);
            }

            virtual void waitUntilNotEmpty(unsigned long millis) const {
                seda::Lock lock(_mtx);
                unsigned long long now(seda::getCurrentTimeMilliseconds());
                while (empty()) {
                    _notEmptyCond.wait(_mtx, millis);
                    if (millis != WAIT_INFINITE &&
                            (seda::getCurrentTimeMilliseconds() - now) > millis)
                        break;
                }
            }

            /**
              Removes all elements from the queue.

Warning: elements will be deleted!
*/
            virtual void clear() {
                seda::Lock lock(_mtx);
                while (!empty()) {
                    IEvent::Ptr e = _list.front();
                    _list.pop_front();
                }
            }

            virtual void wakeUpAll() {
                seda::Lock lock(_mtx);
                _notEmptyCond.notifyAll();
                _emptyCond.notifyAll();
            }

            virtual std::size_t size() const { return _list.size(); }
            bool empty() const { return _list.empty(); }

            std::size_t maxQueueSize() const { return _maxQueueSize; }
            void maxQueueSize(const std::size_t& max) { _maxQueueSize = max; }
        protected:
            SEDA_DECLARE_LOGGER();
            mutable seda::Mutex _mtx;
            mutable seda::Condition _emptyCond;
            mutable seda::Condition _notEmptyCond;

            std::list< IEvent::Ptr > _list;
        private:
            std::string _name;
            std::size_t _maxQueueSize;
    };
}

#endif

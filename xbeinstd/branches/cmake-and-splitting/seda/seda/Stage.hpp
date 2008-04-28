#ifndef SEDA_STAGE_HPP
#define SEDA_STAGE_HPP 1

#include <string>
#include <list>
#include <tr1/memory>

#include <seda/common.hpp>
#include <seda/constants.hpp>
#include <seda/SedaException.hpp>
#include <seda/StageNotFound.hpp>
#include <seda/IEvent.hpp>
#include <seda/IEventQueue.hpp>
#include <seda/Strategy.hpp>

namespace seda {
    class StageWorker;

    class Stage {
    public:
        typedef std::tr1::shared_ptr<Stage> Ptr;
        typedef std::list<StageWorker*> ThreadPool;
    
        Stage(const std::string& name, Strategy::Ptr strategy, std::size_t maxPoolSize=1, std::size_t maxQueueSize=SEDA_MAX_QUEUE_SIZE);
        Stage(const std::string& name, IEventQueue::Ptr queue, Strategy::Ptr strategy, std::size_t maxPoolSize=1);
    
        virtual ~Stage();

        virtual void start();
        virtual void stop();
        virtual void waitUntilEmpty() const { queue()->waitUntilEmpty(); }
        virtual void waitUntilEmpty(unsigned long millis) { queue()->waitUntilEmpty(millis); }
    
        virtual void waitUntilNoneEmpty() const { queue()->waitUntilNotEmpty(); }
        virtual void waitUntilNoneEmpty(unsigned long millis) { queue()->waitUntilNotEmpty(millis); }

        virtual const std::string& name() const { return _name; }
    
        virtual IEventQueue::Ptr queue() { return _queue; }
        virtual const IEventQueue::Ptr queue() const { return _queue; }
        virtual Strategy::Ptr strategy() { return _strategy; }
        virtual const Strategy::Ptr strategy() const { return _strategy; }

        virtual void send(const IEvent::Ptr& e) throw (QueueFull) {
            queue()->push(e);
        }
        static void send(const std::string& stageName, const IEvent::Ptr& e) throw (QueueFull, StageNotFound);
        
        virtual IEvent::Ptr recv(unsigned long millis) throw (QueueEmpty) {
            return queue()->pop(millis);
        }

        unsigned long timeout() const { return _timeout; }
        void timeout(unsigned long millis) { _timeout = millis; }
    private:
        DECLARE_LOGGER();
        IEventQueue::Ptr _queue;
        Strategy::Ptr _strategy;
        std::string _name;
        std::size_t _maxPoolSize;
        unsigned long _timeout;
        ThreadPool _threadPool;
    };
}

#endif // !SEDA_STAGE_HPP

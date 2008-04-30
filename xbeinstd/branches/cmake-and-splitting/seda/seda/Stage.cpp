#include "Stage.hpp"
#include "IEvent.hpp"
#include "StageWorker.hpp"
#include "EventQueue.hpp"
#include "StageRegistry.hpp"

namespace seda {
    Stage::Stage(const std::string& name, Strategy::Ptr strategy, std::size_t maxPoolSize, std::size_t maxQueueSize)
        : INIT_LOGGER("seda.stage."+name),
          _queue(new EventQueue("seda.stage."+name+".queue", maxQueueSize)),
          _strategy(strategy),
          _name(name),
          _maxPoolSize(maxPoolSize),
          _timeout(SEDA_DEFAULT_TIMEOUT)
    {
    }

    Stage::Stage(const std::string& name, IEventQueue::Ptr queue, Strategy::Ptr strategy, std::size_t maxPoolSize)
        : INIT_LOGGER("seda.stage."+name),
          _queue(queue),
          _strategy(strategy),
          _name(name),
          _maxPoolSize(maxPoolSize),
          _timeout(SEDA_DEFAULT_TIMEOUT)
    {
    }
  
    Stage::~Stage() {
        try {
            // stop the running threads and delete them
            stop();
        } catch (const std::exception& e) {
            LOG_ERROR("stopping failed: " << e.what());
        } catch (...) {
            LOG_ERROR("stopping failed: unknown reason");
        }

        try {
            /* log input queue if not empty */
            if (!queue()->empty()) {
                LOG_DEBUG("cleaning up input queue");
                while (!queue()->empty()) {
                    IEvent::Ptr e(queue()->pop());
                    LOG_DEBUG("removed incoming event: " << e->str());
                }
                LOG_DEBUG("done");
            }
        } catch (...) {}
    }

    void
    Stage::start() {
        if (_threadPool.empty()) {
            // initialize and start worker threads
            for (std::size_t tId = 0; tId < _maxPoolSize; ++tId) {
                std::ostringstream sstr;
                sstr << "seda.stage." << name() << ".worker." << tId;
                _threadPool.push_back(new StageWorker(sstr.str(), this));
                _threadPool.back()->start();
            }
        } // else == noop
    }

    void
    Stage::stop() {
        for (ThreadPool::iterator it(_threadPool.begin()); it != _threadPool.end(); ++it) {
            (*it)->stop(); // signal threads to stop
        }
        queue()->notifyAll(); // release blocked threads

        while (!_threadPool.empty()) {
            StageWorker* w(_threadPool.front()); _threadPool.pop_front();
            if (w->id() != activemq::concurrent::Thread::getId()) {
                w->join(); delete w;
            } else {
                LOG_FATAL("StageWorker performed cleanup of its own stage!!!");
                exit(EXIT_FAILURE);
            }
        }
    }

    void
    Stage::send(const std::string& stageName, const seda::IEvent::Ptr& e) throw (QueueFull, StageNotFound) {
        StageRegistry::instance().lookup(stageName)->send(e);
    }
}

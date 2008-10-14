#ifndef SEDA_STAGE_WORKER_HPP
#define SEDA_STAGE_WORKER_HPP

#include <seda/common.hpp>
#include <seda/Thread.hpp>

namespace seda {
    class Stage;
  
    class StageWorker : public seda::Thread {
    public:
        StageWorker(const std::string& id, Stage* s) :
            SEDA_INIT_LOGGER(id),
            _stage(s),
            _busy(false),
            _stopped(false)
        { }
        ~StageWorker() {}

        void stop() { _stopped = true; }
        void operator()() { run(); }
        void run();
        bool busy() const { return _busy; }

    private:
        SEDA_DECLARE_LOGGER();
        bool stopped() { return _stopped; }
      
        Stage* _stage;
        bool _busy;
        bool _stopped;
    };
}

#endif // !SEDA_STAGE_WORKER_HPP

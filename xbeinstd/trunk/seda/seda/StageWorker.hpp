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
            _stopped(false),
            _id(0)
        { }
        ~StageWorker() {}

        void stop() { _stopped = true; }
        void run();
        bool busy() const { return _busy; }
        unsigned long id() const { return _id; }

    private:
        SEDA_DECLARE_LOGGER();
        bool stopped() { return _stopped; }
      
        Stage* _stage;
        bool _busy;
        bool _stopped;
        unsigned long _id;
    };
}

#endif // !SEDA_STAGE_WORKER_HPP

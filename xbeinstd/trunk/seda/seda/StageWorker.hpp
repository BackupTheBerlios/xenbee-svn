#ifndef SEDA_STAGE_WORKER_HPP
#define SEDA_STAGE_WORKER_HPP

#include <seda/logging.hpp>
#include <activemq/concurrent/Thread.h>

namespace seda {
  class Stage;
  
  class StageWorker : public activemq::concurrent::Thread {
  public:
    StageWorker(const std::string& id, Stage* s) :
      INIT_LOGGER(id),
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
    DECLARE_LOGGER();
    bool stopped() { return _stopped; }

    Stage* _stage;
    bool _busy;
    bool _stopped;
    unsigned long _id;
  };
}

#endif // !SEDA_STAGE_WORKER_HPP

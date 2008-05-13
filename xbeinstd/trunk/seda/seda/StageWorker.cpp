#include "StageWorker.hpp"
#include "Stage.hpp"
#include "IEvent.hpp"

namespace seda {
    void StageWorker::run() {
        _id = activemq::concurrent::Thread::getId();

        while (!stopped()) {
            try {
                IEvent::Ptr e = _stage->queue()->pop(_stage->timeout());
                _busy = true; SEDA_LOG_DEBUG("got work");
                _stage->strategy()->perform(e);
                _busy = false; SEDA_LOG_DEBUG("done");
            } catch (const seda::QueueEmpty&) {
                // ignore
            } catch (const seda::QueueFull& qf) {
                SEDA_LOG_ERROR("event discarded due to overflow protection");
            } catch (const std::exception& ex) {
                SEDA_LOG_ERROR("strategy execution failed: " << ex.what());
            } catch (...) {
                SEDA_LOG_ERROR("strategy execution failed: unknown reason");
            }
        }
        SEDA_LOG_DEBUG("terminating");
    }
}

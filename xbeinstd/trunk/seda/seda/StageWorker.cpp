#include "StageWorker.hpp"
#include "Stage.hpp"
#include "IEvent.hpp"
#include "SystemEvent.hpp"
#include "StageRegistry.hpp"

namespace seda {
    void StageWorker::run() {

        while (!stopped()) {
            try {
                IEvent::Ptr e = _stage->queue()->pop(_stage->timeout());
                _busy = true; SEDA_LOG_DEBUG("got work: " << e->str());
                
                // handle system events:
                if (SystemEvent *se = dynamic_cast<SystemEvent*>(e.get())) {
                    // check if there is a system-event-handler stage
                    Stage::Ptr systemEventHandler(StageRegistry::instance().lookup(_stage->getErrorHandler()));
                    if (systemEventHandler) {
                        // is our own stage the system-event-handler?
                        if (systemEventHandler.get() == _stage) {
                            _stage->strategy()->perform(e);
                        } else {
                            systemEventHandler->send(e);
                        }
                    } else {
                        SEDA_LOG_FATAL("received a SystemEvent, but no system-event-handler has been registered!");
                    }
                } else {
                    _stage->strategy()->perform(e);
                }
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

#include "DeserializeStrategy.hpp"

#include "xbemsg.pb.h"
#include "event/DecodedMessageEvent.hpp"
#include "event/EncodedMessageEvent.hpp"

#include "event/ErrorMessageEvent.hpp"

#include "event/ExecuteEvent.hpp"
#include "event/ExecuteAckEvent.hpp"

#include "event/FailedEvent.hpp"
#include "event/FailedAckEvent.hpp"

#include "event/FinishedEvent.hpp"
#include "event/FinishedAckEvent.hpp"

#include "event/LifeSignEvent.hpp"

#include "event/ShutdownEvent.hpp"
#include "event/ShutdownAckEvent.hpp"

#include "event/StatusEvent.hpp"
#include "event/StatusReqEvent.hpp"

#include "event/TerminateEvent.hpp"
#include "event/TerminateAckEvent.hpp"


using namespace xbe;

DeserializeStrategy::DeserializeStrategy(const std::string &name,
                                         const std::string &next)
    : seda::ForwardStrategy(next), XBE_INIT_LOGGER(name) {}

void DeserializeStrategy::perform(const seda::IEvent::Ptr &e) {
    
}

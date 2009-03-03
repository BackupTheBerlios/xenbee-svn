#include "DeserializeStrategy.hpp"

#include "xbemsg.pb.h"
#include "event/DecodedMessageEvent.hpp"
#include "event/EncodedMessageEvent.hpp"

#include "event/ErrorMessageEvent.hpp"

#include "event/ExecuteEvent.hpp"
#include "event/ExecuteAckEvent.hpp"
#include "event/ExecuteNakEvent.hpp"

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
using namespace xbe::event;
using namespace xbe::messages;

DeserializeStrategy::DeserializeStrategy(const std::string &name,
                                         const std::string &next)
    : seda::ForwardStrategy(next), XBE_INIT_LOGGER(name) {}

void DeserializeStrategy::perform(const seda::IEvent::Ptr &e) {
    if (EncodedMessageEvent *eme = dynamic_cast<EncodedMessageEvent*>(e.get())) {
        xbe::event::DecodedMessageEvent::Ptr dme;

        std::string msg(eme->message());
        XbeMessage xbeMsg;
        if (! xbeMsg.ParseFromString(msg)) {
            XBE_LOG_WARN("could not parse the EncodedMessageEvent, dropping it: " << e->str());
            return;
        }

        if (xbeMsg.has_error()) {
            dme = ErrorMessageEvent::deserialize(msg);
        } else if (xbeMsg.has_execute()) {
            dme = ExecuteEvent::deserialize(msg);
        } else if (xbeMsg.has_execute_ack()) {
            dme = ExecuteAckEvent::deserialize(msg);
        } else if (xbeMsg.has_execute_nak()) {
            dme = ExecuteNakEvent::deserialize(msg);
        } else if (xbeMsg.has_status_req()) {
            dme = StatusReqEvent::deserialize(msg);
        } else if (xbeMsg.has_status()) {
            dme = StatusEvent::deserialize(msg);
        } else if (xbeMsg.has_finished()) {
            dme = FinishedEvent::deserialize(msg);
        } else if (xbeMsg.has_finished_ack()) {
            dme = FinishedAckEvent::deserialize(msg);
        } else if (xbeMsg.has_failed()) {
            dme = FailedEvent::deserialize(msg);
        } else if (xbeMsg.has_failed_ack()) {
            dme = FailedAckEvent::deserialize(msg);
        } else if (xbeMsg.has_shutdown()) {
            dme = ShutdownEvent::deserialize(msg);
        } else if (xbeMsg.has_shutdown_ack()) {
            dme = ShutdownAckEvent::deserialize(msg);
        } else if (xbeMsg.has_terminate()) {
            dme = TerminateEvent::deserialize(msg);
        } else if (xbeMsg.has_terminate_ack()) {
            dme = TerminateAckEvent::deserialize(msg);
        } else if (xbeMsg.has_life_sign()) {
            dme = LifeSignEvent::deserialize(msg);
        }

        if (dme) {
            if (eme->source().isValid())
                dme->source(eme->source());
            if (eme->destination().isValid())
                dme->destination(eme->destination());

            XBE_LOG_DEBUG("deserialized event: " << dme->str());
            ForwardStrategy::perform(dme);
        } else {
            XBE_LOG_WARN("got an EncodedMessageEvent that could not be decoded: " << e->str());
        }
    } else {
        XBE_LOG_WARN("received event that is not of type EncodedMessageEvent, dropping it.");
    }
}

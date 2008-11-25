#include "XbeInstd.hpp"
#include <seda/TimerEvent.hpp>
#include "xbe/event/ShutdownAckEvent.hpp"
#include "xbe/event/StatusEvent.hpp"
#include "xbe/event/TerminateAckEvent.hpp"

using namespace xbe;

XbeInstd::XbeInstd(const std::string &name, const std::string &nextStage,
                   const std::string &to, const std::string &from,
                   const boost::posix_time::time_duration &lifeSignInterval,
                   std::size_t maxRetries)
    : seda::ForwardStrategy(name, nextStage),
      XBE_INIT_LOGGER("xbe.xbeinstd"),
      _fsm(*this),
      _timeoutTimer(name, boost::posix_time::seconds(5), "timeout"),
      _lifeSignTimer(name, lifeSignInterval, "lifeSign"),
      _to(to), _from(from),
      _maxRetries(maxRetries),
      _retryCounter(0)
{
}

void XbeInstd::perform(const seda::IEvent::Ptr &e) const {
    XbeInstd *inst(const_cast<XbeInstd*>(this));
    if (seda::TimerEvent* evt = dynamic_cast<seda::TimerEvent*>(e.get())) {
        if (evt->tag() == "lifeSign") {
            inst->_fsm.LifeSign();
        } else if (evt->tag() == "timeout") {
            inst->_fsm.Timeout();
        }
    } else if (xbe::event::ExecuteEvent* evt = dynamic_cast<xbe::event::ExecuteEvent*>(e.get())) {
        inst->_fsm.Execute(*evt);
    } else if (xbe::event::TerminateEvent* evt = dynamic_cast<xbe::event::TerminateEvent*>(e.get())) {
        inst->_fsm.Terminate(*evt);
    } else if (xbe::event::ShutdownEvent* evt = dynamic_cast<xbe::event::ShutdownEvent*>(e.get())) {
        inst->_fsm.Shutdown(*evt);
    } else if (xbe::event::StatusReqEvent* evt = dynamic_cast<xbe::event::StatusReqEvent*>(e.get())) {
        inst->_fsm.StatusReq(*evt);
    } else if (xbe::event::FinishedAckEvent* evt = dynamic_cast<xbe::event::FinishedAckEvent*>(e.get())) {
        inst->_fsm.FinishedAck(*evt);
/*
    } else if (xbe::event::FailedAckEvent* evt = dynamic_cast<xbe::event::FailedAckEvent*>(e.get())) {
        inst->_fsm.FailedAck(*evt);
*/

    }
}

void XbeInstd::do_execute(xbe::event::ExecuteEvent&) {
}

void XbeInstd::do_terminate(xbe::event::TerminateEvent&) {
    XBE_LOG_DEBUG("sending terminate-ack");
    seda::IEvent::Ptr e(new xbe::event::TerminateAckEvent(_to, _from, "1"));
    ForwardStrategy::perform(e);
}

void XbeInstd::do_terminate_job() {
    XBE_LOG_DEBUG("terminating task");
}

void XbeInstd::do_shutdown(xbe::event::ShutdownEvent& shutdownEvent) {
    XBE_LOG_DEBUG("sending shutdown-ack");
    seda::IEvent::Ptr e(new xbe::event::ShutdownAckEvent(_to, _from, "1"));
    ForwardStrategy::perform(e);
}

void XbeInstd::do_send_status(xbe::event::StatusReqEvent&) {
    XBE_LOG_DEBUG("sending status");
    seda::IEvent::Ptr e(new xbe::event::StatusEvent(_to, _from, "1"));
    ForwardStrategy::perform(e);
}

void XbeInstd::do_finished_ack(xbe::event::FinishedAckEvent&) {}

void XbeInstd::do_failed_ack(xbe::event::FailedAckEvent&) {}

/* regular events */
void XbeInstd::do_send_lifesign() {
    XBE_LOG_DEBUG("sending life sign");
    ForwardStrategy::perform(seda::IEvent::Ptr(new xbe::event::LifeSignEvent(_to, _from, "1")));
}

/* events coming from the executed job */
void XbeInstd::do_task_finished() {

}
void XbeInstd::do_task_failed() {

}

void XbeInstd::do_failed() {

}

void XbeInstd::do_start_timer() {
    _timeoutTimer.start();
}
void XbeInstd::do_stop_timer() {
    _timeoutTimer.stop();
}

void XbeInstd::do_start_lifesign() {
    XBE_LOG_INFO("starting life sign timer");
    _lifeSignTimer.start();
}
void XbeInstd::do_stop_lifesign() {
    XBE_LOG_INFO("stopping life sign timer");
    _lifeSignTimer.stop();
}

void XbeInstd::onTaskExit(const Task *t) {
    XBE_LOG_INFO("task exited");
}
void XbeInstd::onTaskFailure(const Task *t) {
    XBE_LOG_INFO("task failed");
}

void XbeInstd::onStageStart() {
    XBE_LOG_DEBUG("stage started");
    _fsm.Start();
}

void XbeInstd::onStageStop() {
    XBE_LOG_DEBUG("stage stopped");
    do_stop_lifesign();
}


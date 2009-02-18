#include "XbeInstd.hpp"
#include <signal.h>
#include <seda/TimerEvent.hpp>
#include <seda/StageRegistry.hpp>
#include "xbe/event/ShutdownAckEvent.hpp"
#include "xbe/event/StatusEvent.hpp"
#include "xbe/event/TerminateAckEvent.hpp"
#include "xbe/event/TaskFinishedEvent.hpp"
#include "xbe/event/ExecuteAckEvent.hpp"

using namespace xbe;

XbeInstd::XbeInstd(const std::string &name, const seda::Strategy::Ptr &decorated,
                   const std::string &to, const std::string &from,
                   const boost::posix_time::time_duration &lifeSignInterval,
                   std::size_t maxRetries)
    : seda::StrategyDecorator(name, decorated),
      XBE_INIT_LOGGER("xbe.xbeinstd"),
      _fsm(*this),
      _timeoutTimer(name, boost::posix_time::seconds(5), "timeout"),
      _lifeSignTimer(name, lifeSignInterval, "lifeSign"),
      _to(to), _from(from),
      _maxRetries(maxRetries),
      _retryCounter(0),
      _mainTask((xbe::Task*)0),
      _statusTask((xbe::Task*)0)
{
}

void XbeInstd::perform(const seda::IEvent::Ptr &e) {
    boost::unique_lock<boost::recursive_mutex> lock(_mtx);
    if (seda::TimerEvent* evt = dynamic_cast<seda::TimerEvent*>(e.get())) {
        if (evt->tag() == "lifeSign") {
            _fsm.LifeSign();
        } else if (evt->tag() == "timeout") {
            _fsm.Timeout();
        }
    } else if (xbe::event::ExecuteEvent* evt = dynamic_cast<xbe::event::ExecuteEvent*>(e.get())) {
        _fsm.Execute(*evt);
    } else if (xbe::event::TerminateEvent* evt = dynamic_cast<xbe::event::TerminateEvent*>(e.get())) {
        _fsm.Terminate(*evt);
    } else if (xbe::event::ShutdownEvent* evt = dynamic_cast<xbe::event::ShutdownEvent*>(e.get())) {
        _fsm.Shutdown(*evt);
    } else if (xbe::event::StatusReqEvent* evt = dynamic_cast<xbe::event::StatusReqEvent*>(e.get())) {
        _fsm.StatusReq(*evt);
    } else if (xbe::event::FinishedAckEvent* evt = dynamic_cast<xbe::event::FinishedAckEvent*>(e.get())) {
        _fsm.FinishedAck(*evt);
    } else if (xbe::event::TaskFinishedEvent* evt = dynamic_cast<xbe::event::TaskFinishedEvent*>(e.get())) {
        _fsm.Finished(evt->exitcode());
/*
    } else if (xbe::event::FailedAckEvent* evt = dynamic_cast<xbe::event::FailedAckEvent*>(e.get())) {
        _fsm.FailedAck(*evt);
*/

    }
}

void XbeInstd::do_execute(xbe::event::ExecuteEvent& e) {
    XBE_LOG_DEBUG("executing task");
    _mainTask = std::tr1::shared_ptr<xbe::Task>(new xbe::Task(e.taskData()));
    _mainTask->setTaskListener(this);

    // create the status query task if available
    if (e.statusTaskData().is_valid()) {
        _statusTask = std::tr1::shared_ptr<xbe::Task>(new xbe::Task(e.statusTaskData()));
//        _statusTask->setTaskListener(this);
    }

    _mainTask->run();
}

void XbeInstd::do_terminate() {
    XBE_LOG_DEBUG("sending terminate-ack");
    seda::IEvent::Ptr e(new xbe::event::TerminateAckEvent(_to, _from, "1"));
    StrategyDecorator::perform(e);
}

void XbeInstd::do_terminate_job(int signal) {
    XBE_LOG_DEBUG("terminating task");
    assert(_mainTask.get() != NULL);
    _mainTask->kill(signal);
}

void XbeInstd::do_shutdown(xbe::event::ShutdownEvent& shutdownEvent) {
    XBE_LOG_DEBUG("sending shutdown-ack");
    seda::IEvent::Ptr e(new xbe::event::ShutdownAckEvent(_to, _from, "1"));
    StrategyDecorator::perform(e);
}

void XbeInstd::do_send_status(xbe::event::StatusReqEvent&, xbe::event::StatusEvent::Status st) {
    std::tr1::shared_ptr<xbe::event::StatusEvent> e(new xbe::event::StatusEvent(_to, _from, "1", time(0)));
    e->state(st);

    if (_statusTask) {
        XBE_LOG_DEBUG("running user-defined status query");
        _statusTask->run(); _statusTask->wait();
        e->taskStatusCode(_statusTask->exitcode());
        e->taskStatusStdOut(_statusTask->stdout());
        e->taskStatusStdErr(_statusTask->stderr());
    }

    XBE_LOG_DEBUG("sending status");
    StrategyDecorator::perform(e);
}
void XbeInstd::do_send_execute_ack(xbe::event::ExecuteEvent&) {
    XBE_LOG_DEBUG("sending execute-ack");
    seda::IEvent::Ptr e(new xbe::event::ExecuteAckEvent(_to, _from, "1"));
    StrategyDecorator::perform(e);
}

void XbeInstd::do_finished_ack(xbe::event::FinishedAckEvent&) {
    XBE_LOG_DEBUG("got finished-ack");
}

void XbeInstd::do_failed_ack(xbe::event::FailedAckEvent&) {
    XBE_LOG_DEBUG("got failed-ack");
}

/* regular events */
void XbeInstd::do_send_lifesign() {
    XBE_LOG_DEBUG("sending life sign");
    StrategyDecorator::perform(seda::IEvent::Ptr(new xbe::event::LifeSignEvent(_to, _from, "1", time(0))));
}

/* events comming from the executed job */
void XbeInstd::do_task_finished(int exitcode) {
    XBE_LOG_DEBUG("sending finished event");
    seda::IEvent::Ptr e(new xbe::event::FinishedEvent(_to, _from, "1", exitcode));
    StrategyDecorator::perform(e);
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
    try {
        seda::IEvent::Ptr e(new xbe::event::TaskFinishedEvent(t->exitcode()));
        seda::StageRegistry::instance().lookup(_stageName)->send(e);
    } catch (...) {
        XBE_LOG_ERROR("task exited but event could not be sent to own stage!");
    }
}
void XbeInstd::onTaskFailure(const Task *t) {
    XBE_LOG_INFO("task failed");
}

void XbeInstd::onStageStart(const std::string &stageName) {
    boost::unique_lock<boost::recursive_mutex> lock(_mtx);
    XBE_LOG_DEBUG("stage started");
    _stageName = stageName;
    _fsm.Start();
}

void XbeInstd::onStageStop(const std::string &) {
    boost::unique_lock<boost::recursive_mutex> lock(_mtx);
    XBE_LOG_DEBUG("stage stopping");
    do_stop_lifesign();
    do_stop_timer();
}

void XbeInstd::wait() {
    boost::unique_lock<boost::recursive_mutex> lock(_mtx);
    while (true) {
        _shutdown.wait(lock);
    }
}

void XbeInstd::wait(unsigned long millis) {
    boost::unique_lock<boost::recursive_mutex> lock(_mtx);
    boost::system_time const timeout=boost::get_system_time() + boost::posix_time::milliseconds(millis);
    _shutdown.timed_wait(lock, timeout);
}


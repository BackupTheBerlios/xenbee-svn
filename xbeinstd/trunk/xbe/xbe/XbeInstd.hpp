#ifndef XBE_XBEINSTD_HPP
#define XBE_XBEINSTD_HPP 1

#include <boost/thread.hpp>

#include <seda/StrategyDecorator.hpp>
#include <seda/Timer.hpp>

#include <xbe/event/ExecuteEvent.hpp>
#include <xbe/event/LifeSignEvent.hpp>
#include <xbe/event/StatusReqEvent.hpp>
#include <xbe/event/StatusEvent.hpp>
#include <xbe/event/TerminateEvent.hpp>
#include <xbe/event/FinishedEvent.hpp>
#include <xbe/event/FinishedAckEvent.hpp>
#include <xbe/event/FailedEvent.hpp>
#include <xbe/event/FailedAckEvent.hpp>
#include <xbe/event/ShutdownEvent.hpp>

#include <xbe/Task.hpp>
#include <xbe/XbeInstd_sm.h>

namespace xbe {
    class XbeInstd : public seda::StrategyDecorator, public xbe::TaskListener {
        public:
            typedef std::tr1::shared_ptr<XbeInstd> Ptr;

            XbeInstd(const std::string &name, const seda::Strategy::Ptr &decorated,
                     const std::string &to, const std::string &from, const std::string &conversation_id,
                     const boost::posix_time::time_duration &lifeSignInterval = boost::posix_time::seconds(3),
                     std::size_t maxRetries = 5);

            virtual ~XbeInstd() {
                _timeoutTimer.stop();
                _lifeSignTimer.stop();            
            }
            virtual void perform(const seda::IEvent::Ptr &e);

            /* events from the xbed */
            void do_execute(xbe::event::ExecuteEvent&);
            void do_terminate();
            void do_terminate_job(int signal);
            void do_shutdown(xbe::event::ShutdownEvent&);
            void do_send_status(xbe::event::StatusReqEvent&, xbe::event::StatusEvent::StatusCode);
            void do_send_execute_ack(xbe::event::ExecuteEvent&);
            void do_send_execute_nak(xbe::event::ExecuteEvent&);
            void do_finished_ack(xbe::event::FinishedAckEvent&);
            void do_failed_ack(xbe::event::FailedAckEvent&);

            /* regular events */
            void do_send_lifesign();

            /* events coming from the executed job */
            void do_task_finished(int exitcode);
            void do_task_failed();

            void do_failed();

            void do_start_timer();
            void do_stop_timer();

            void do_start_lifesign();
            void do_stop_lifesign();

            void inc_retryCounter() { _retryCounter++; }
            void reset_retryCounter() { _retryCounter = 0; }
            std::size_t retryCounter() const { return _retryCounter; };
            std::size_t maxRetries() const { return _maxRetries; }

            virtual void onTaskExit(const Task *t);
            virtual void onTaskFailure(const Task *t);

            virtual void onStageStart(const std::string &);
            virtual void onStageStop(const std::string &);

            void wait();
            void wait(unsigned long millis);

            bool is_stopped() const { return _stopped; }
        private:
            XBE_DECLARE_LOGGER();
            XbeInstdContext _fsm;

            seda::Timer _timeoutTimer;
            seda::Timer _lifeSignTimer;
            std::string _to;
            std::string _from;
            std::string _conversation_id;
            std::string _stageName;
            std::size_t _maxRetries;
            std::size_t _retryCounter;
            bool _stopped;

            std::tr1::shared_ptr<xbe::Task> _mainTask;
            std::tr1::shared_ptr<xbe::Task> _statusTask;

            boost::recursive_mutex _mtx;
            boost::condition_variable_any _shutdown;
    };
}

#endif // XBE_XBEINSTD_HPP

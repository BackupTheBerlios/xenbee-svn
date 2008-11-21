#ifndef XBE_XBEINSTD_HPP
#define XBE_XBEINSTD_HPP 1

#include <xbe/event/ExecuteEvent.hpp>
#include <xbe/event/LifeSignEvent.hpp>
#include <xbe/event/StatusReqEvent.hpp>
#include <xbe/event/TerminateEvent.hpp>
#include <xbe/event/FinishedEvent.hpp>
#include <xbe/event/FinishedAckEvent.hpp>
#include <xbe/event/FailedEvent.hpp>
#include <xbe/event/FailedAckEvent.hpp>
#include <xbe/event/ShutdownEvent.hpp>

namespace xbe {
    class XbeInstd {
        public:
            /* events from the xbed */
            void do_execute(xbe::event::ExecuteEvent&);
            void do_terminate(xbe::event::TerminateEvent&);
            void do_terminate_job();
            void do_shutdown(xbe::event::ShutdownEvent&);
            void do_send_status(xbe::event::StatusReqEvent&);
            void do_finished_ack(xbe::event::FinishedAckEvent&);
            void do_failed_ack(xbe::event::FailedAckEvent&);

            /* regular events */
            void do_send_lifesign();

            /* events coming from the executed job */
            void do_task_finished();
            void do_task_failed();

            void do_failed();
            void do_stop_timer();

            std::size_t retryCounter() const;
            std::size_t maxRetries() const;
    };
}

#endif // XBE_XBEINSTD_HPP

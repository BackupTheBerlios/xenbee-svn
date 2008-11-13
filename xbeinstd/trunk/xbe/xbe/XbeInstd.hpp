#ifndef XBE_XBEINSTD_HPP
#define XBE_XBEINSTD_HPP 1

#include <xbe/event/ExecuteEvent.hpp>
#include <xbe/event/LifeSignEvent.hpp>
#include <xbe/event/StatusReqEvent.hpp>
#include <xbe/event/TerminateEvent.hpp>
#include <xbe/event/FinishedEvent.hpp>
#include <xbe/event/FailedEvent.hpp>

namespace xbe {
    class XbeInstd {
        public:
            /* events from the xbed */
            void do_execute(const xbe::event::ExecuteEvent&);
            void do_terminate(const xbe::event::TerminateEvent&);
            void do_terminate_job();
            void do_send_status(const xbe::event::StatusReqEvent&);

            /* regular events */
            void do_send_lifesign(const xbe::event::LifeSignEvent&);

            /* events coming from the executed job */
            void do_finished(const xbe::event::FinishedEvent&);
            void do_failed(const xbe::event::FailedEvent&);
    };
}

#endif // XBE_XBEINSTD_HPP

#ifndef XBE_XBEINSTD_HPP
#define XBE_XBEINSTD_HPP 1

#include <xbe/ExecuteEvent.hpp>
#include <xbe/LifeSignEvent.hpp>
#include <xbe/StatusReqEvent.hpp>
#include <xbe/TerminateEvent.hpp>
#include <xbe/FinishedEvent.hpp>
#include <xbe/FailedEvent.hpp>

namespace xbe {
    class XbeInstd {
        public:
            /* events from the xbed */
            void do_execute(const xbe::ExecuteEvent&);
            void do_terminate(const xbe::TerminateEvent&);
            void do_terminate_job();
            void do_send_status(const xbe::StatusReqEvent&);

            /* regular events */
            void do_send_lifesign(const xbe::LifeSignEvent&);

            /* events coming from the executed job */
            void do_finished(const xbe::FinishedEvent&);
            void do_failed(const xbe::FailedEvent&);
    };
}

#endif // XBE_XBEINSTD_HPP

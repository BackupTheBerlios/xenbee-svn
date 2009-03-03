
//
// Finite state machine for the XbeInstd
//


#include <xbe/event/ExecuteEvent.hpp>
#include <xbe/event/ShutdownEvent.hpp>
#include <xbe/event/LifeSignEvent.hpp>
#include <xbe/event/StatusReqEvent.hpp>
#include <xbe/event/TerminateEvent.hpp>
#include <xbe/event/FinishedEvent.hpp>
#include <xbe/event/FinishedAckEvent.hpp>
#include <xbe/event/FailedEvent.hpp>
#include <xbe/event/FailedAckEvent.hpp>
#include <xbe/event/StatusEvent.hpp>
#include <signal.h>
#include "XbeInstd.hpp"
#include "XbeInstd_sm.h"

using namespace statemap;

namespace xbe
{
    // Static class declarations.
    XbeInstdFSM_Init XbeInstdFSM::Init("XbeInstdFSM::Init", 0);
    XbeInstdFSM_Idle XbeInstdFSM::Idle("XbeInstdFSM::Idle", 1);
    XbeInstdFSM_Busy XbeInstdFSM::Busy("XbeInstdFSM::Busy", 2);
    XbeInstdFSM_WaitForTaskTermination XbeInstdFSM::WaitForTaskTermination("XbeInstdFSM::WaitForTaskTermination", 3);
    XbeInstdFSM_WaitForFinishedAck XbeInstdFSM::WaitForFinishedAck("XbeInstdFSM::WaitForFinishedAck", 4);
    XbeInstdFSM_Shutdown XbeInstdFSM::Shutdown("XbeInstdFSM::Shutdown", 5);
    XbeInstdFSM_Failed XbeInstdFSM::Failed("XbeInstdFSM::Failed", 6);

    void XbeInstdState::Execute(XbeInstdContext& context, xbe::event::ExecuteEvent& msg)
    {
        Default(context);
        return;
    }

    void XbeInstdState::Finished(XbeInstdContext& context, int exitcode)
    {
        Default(context);
        return;
    }

    void XbeInstdState::FinishedAck(XbeInstdContext& context, xbe::event::FinishedAckEvent& msg)
    {
        Default(context);
        return;
    }

    void XbeInstdState::LifeSign(XbeInstdContext& context)
    {
        Default(context);
        return;
    }

    void XbeInstdState::Shutdown(XbeInstdContext& context, xbe::event::ShutdownEvent& msg)
    {
        Default(context);
        return;
    }

    void XbeInstdState::Start(XbeInstdContext& context)
    {
        Default(context);
        return;
    }

    void XbeInstdState::StatusReq(XbeInstdContext& context, xbe::event::StatusReqEvent& msg)
    {
        Default(context);
        return;
    }

    void XbeInstdState::Terminate(XbeInstdContext& context)
    {
        Default(context);
        return;
    }

    void XbeInstdState::Terminate(XbeInstdContext& context, xbe::event::TerminateEvent& msg)
    {
        Default(context);
        return;
    }

    void XbeInstdState::Timeout(XbeInstdContext& context)
    {
        Default(context);
        return;
    }

    void XbeInstdState::Default(XbeInstdContext& context)
    {
        throw (
            TransitionUndefinedException(
                context.getState().getName(),
                context.getTransition()));

        return;
    }

    void XbeInstdFSM_Default::Execute(XbeInstdContext& context, xbe::event::ExecuteEvent& msg)
    {


        return;
    }

    void XbeInstdFSM_Default::LifeSign(XbeInstdContext& context)
    {
        XbeInstd& ctxt(context.getOwner());

        XbeInstdState& EndStateName = context.getState();

        context.clearState();
        try
        {
            ctxt.do_send_lifesign();
            context.setState(EndStateName);
        }
        catch (...)
        {
            context.setState(EndStateName);
            throw;
        }

        return;
    }

    void XbeInstdFSM_Init::Start(XbeInstdContext& context)
    {
        XbeInstd& ctxt(context.getOwner());

        (context.getState()).Exit(context);
        context.clearState();
        try
        {
            ctxt.do_start_lifesign();
            context.setState(XbeInstdFSM::Idle);
        }
        catch (...)
        {
            context.setState(XbeInstdFSM::Idle);
            throw;
        }
        (context.getState()).Entry(context);

        return;
    }

    void XbeInstdFSM_Idle::Execute(XbeInstdContext& context, xbe::event::ExecuteEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        (context.getState()).Exit(context);
        context.clearState();
        try
        {
            ctxt.do_send_execute_ack(msg);
            ctxt.do_execute(msg);
            context.setState(XbeInstdFSM::Busy);
        }
        catch (...)
        {
            context.setState(XbeInstdFSM::Busy);
            throw;
        }
        (context.getState()).Entry(context);

        return;
    }

    void XbeInstdFSM_Idle::Finished(XbeInstdContext& context, int exitcode)
    {


        return;
    }

    void XbeInstdFSM_Idle::FinishedAck(XbeInstdContext& context, xbe::event::FinishedAckEvent& msg)
    {


        return;
    }

    void XbeInstdFSM_Idle::Shutdown(XbeInstdContext& context, xbe::event::ShutdownEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        (context.getState()).Exit(context);
        context.clearState();
        try
        {
            ctxt.do_shutdown(msg);
            context.setState(XbeInstdFSM::Shutdown);
        }
        catch (...)
        {
            context.setState(XbeInstdFSM::Shutdown);
            throw;
        }
        (context.getState()).Entry(context);

        return;
    }

    void XbeInstdFSM_Idle::StatusReq(XbeInstdContext& context, xbe::event::StatusReqEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        XbeInstdState& EndStateName = context.getState();

        context.clearState();
        try
        {
            ctxt.do_send_status(msg, xbe::event::StatusEvent::ST_IDLE);
            context.setState(EndStateName);
        }
        catch (...)
        {
            context.setState(EndStateName);
            throw;
        }

        return;
    }

    void XbeInstdFSM_Idle::Terminate(XbeInstdContext& context, xbe::event::TerminateEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        XbeInstdState& EndStateName = context.getState();

        context.clearState();
        try
        {
            ctxt.do_terminate();
            context.setState(EndStateName);
        }
        catch (...)
        {
            context.setState(EndStateName);
            throw;
        }

        return;
    }

    void XbeInstdFSM_Busy::Execute(XbeInstdContext& context, xbe::event::ExecuteEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        XbeInstdState& EndStateName = context.getState();

        context.clearState();
        try
        {
            ctxt.do_send_execute_nak(msg);
            context.setState(EndStateName);
        }
        catch (...)
        {
            context.setState(EndStateName);
            throw;
        }

        return;
    }

    void XbeInstdFSM_Busy::Finished(XbeInstdContext& context, int exitcode)
    {
        XbeInstd& ctxt(context.getOwner());

        (context.getState()).Exit(context);
        context.clearState();
        try
        {
            ctxt.do_task_finished(exitcode);
            context.setState(XbeInstdFSM::WaitForFinishedAck);
        }
        catch (...)
        {
            context.setState(XbeInstdFSM::WaitForFinishedAck);
            throw;
        }
        (context.getState()).Entry(context);

        return;
    }

    void XbeInstdFSM_Busy::Shutdown(XbeInstdContext& context, xbe::event::ShutdownEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        (context.getState()).Exit(context);
        context.clearState();
        try
        {
            ctxt.do_terminate_job(SIGKILL);
            ctxt.do_shutdown(msg);
            context.setState(XbeInstdFSM::Shutdown);
        }
        catch (...)
        {
            context.setState(XbeInstdFSM::Shutdown);
            throw;
        }
        (context.getState()).Entry(context);

        return;
    }

    void XbeInstdFSM_Busy::StatusReq(XbeInstdContext& context, xbe::event::StatusReqEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        XbeInstdState& EndStateName = context.getState();

        context.clearState();
        try
        {
            ctxt.do_send_status(msg, xbe::event::StatusEvent::ST_RUNNING);
            context.setState(EndStateName);
        }
        catch (...)
        {
            context.setState(EndStateName);
            throw;
        }

        return;
    }

    void XbeInstdFSM_Busy::Terminate(XbeInstdContext& context, xbe::event::TerminateEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        (context.getState()).Exit(context);
        context.clearState();
        try
        {
            ctxt.do_terminate_job(SIGTERM);
            context.setState(XbeInstdFSM::WaitForTaskTermination);
        }
        catch (...)
        {
            context.setState(XbeInstdFSM::WaitForTaskTermination);
            throw;
        }
        (context.getState()).Entry(context);

        return;
    }

    void XbeInstdFSM_WaitForTaskTermination::Entry(XbeInstdContext& context)

{
        XbeInstd& ctxt(context.getOwner());

        ctxt.reset_retryCounter();
        ctxt.do_start_timer();
        return;
    }

    void XbeInstdFSM_WaitForTaskTermination::Exit(XbeInstdContext& context)

{
        XbeInstd& ctxt(context.getOwner());

        ctxt.do_stop_timer();
        return;
    }

    void XbeInstdFSM_WaitForTaskTermination::Finished(XbeInstdContext& context, int exitcode)
    {
        XbeInstd& ctxt(context.getOwner());

        (context.getState()).Exit(context);
        context.clearState();
        try
        {
            ctxt.do_terminate();
            context.setState(XbeInstdFSM::Idle);
        }
        catch (...)
        {
            context.setState(XbeInstdFSM::Idle);
            throw;
        }
        (context.getState()).Entry(context);

        return;
    }

    void XbeInstdFSM_WaitForTaskTermination::StatusReq(XbeInstdContext& context, xbe::event::StatusReqEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        XbeInstdState& EndStateName = context.getState();

        context.clearState();
        try
        {
            ctxt.do_send_status(msg, xbe::event::StatusEvent::ST_RUNNING);
            context.setState(EndStateName);
        }
        catch (...)
        {
            context.setState(EndStateName);
            throw;
        }

        return;
    }

    void XbeInstdFSM_WaitForTaskTermination::Terminate(XbeInstdContext& context)
    {


        return;
    }

    void XbeInstdFSM_WaitForTaskTermination::Timeout(XbeInstdContext& context)
    {
        XbeInstd& ctxt(context.getOwner());

        if (ctxt.retryCounter() < ctxt.maxRetries())
        {
            XbeInstdState& EndStateName = context.getState();

            context.clearState();
            try
            {
                ctxt.do_terminate_job(SIGTERM);
                ctxt.inc_retryCounter();
                context.setState(EndStateName);
            }
            catch (...)
            {
                context.setState(EndStateName);
                throw;
            }
        }
        else
        {
            (context.getState()).Exit(context);
            context.clearState();
            try
            {
                ctxt.do_terminate_job(SIGKILL);
                ctxt.do_terminate();
                context.setState(XbeInstdFSM::Idle);
            }
            catch (...)
            {
                context.setState(XbeInstdFSM::Idle);
                throw;
            }
            (context.getState()).Entry(context);
        }

        return;
    }

    void XbeInstdFSM_WaitForFinishedAck::Entry(XbeInstdContext& context)

{
        XbeInstd& ctxt(context.getOwner());

        ctxt.reset_retryCounter();
        ctxt.do_start_timer();
        return;
    }

    void XbeInstdFSM_WaitForFinishedAck::Exit(XbeInstdContext& context)

{
        XbeInstd& ctxt(context.getOwner());

        ctxt.do_stop_timer();
        return;
    }

    void XbeInstdFSM_WaitForFinishedAck::FinishedAck(XbeInstdContext& context, xbe::event::FinishedAckEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        (context.getState()).Exit(context);
        context.clearState();
        try
        {
            ctxt.do_finished_ack(msg);
            context.setState(XbeInstdFSM::Idle);
        }
        catch (...)
        {
            context.setState(XbeInstdFSM::Idle);
            throw;
        }
        (context.getState()).Entry(context);

        return;
    }

    void XbeInstdFSM_WaitForFinishedAck::Shutdown(XbeInstdContext& context, xbe::event::ShutdownEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        (context.getState()).Exit(context);
        context.clearState();
        try
        {
            ctxt.do_shutdown(msg);
            context.setState(XbeInstdFSM::Shutdown);
        }
        catch (...)
        {
            context.setState(XbeInstdFSM::Shutdown);
            throw;
        }
        (context.getState()).Entry(context);

        return;
    }

    void XbeInstdFSM_WaitForFinishedAck::StatusReq(XbeInstdContext& context, xbe::event::StatusReqEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        XbeInstdState& EndStateName = context.getState();

        context.clearState();
        try
        {
            ctxt.do_send_status(msg, xbe::event::StatusEvent::ST_FINISHED);
            context.setState(EndStateName);
        }
        catch (...)
        {
            context.setState(EndStateName);
            throw;
        }

        return;
    }

    void XbeInstdFSM_WaitForFinishedAck::Terminate(XbeInstdContext& context, xbe::event::TerminateEvent& msg)
    {

        (context.getState()).Exit(context);
        context.setState(XbeInstdFSM::Idle);
        (context.getState()).Entry(context);

        return;
    }

    void XbeInstdFSM_WaitForFinishedAck::Timeout(XbeInstdContext& context)
    {
        XbeInstd& ctxt(context.getOwner());

        if (ctxt.retryCounter() < ctxt.maxRetries())
        {
            XbeInstdState& EndStateName = context.getState();

            context.clearState();
            try
            {
                ctxt.do_task_finished(-1);
                ctxt.inc_retryCounter();
                context.setState(EndStateName);
            }
            catch (...)
            {
                context.setState(EndStateName);
                throw;
            }
        }
        else
        {
            (context.getState()).Exit(context);
            context.clearState();
            try
            {
                ctxt.do_failed();
                context.setState(XbeInstdFSM::Failed);
            }
            catch (...)
            {
                context.setState(XbeInstdFSM::Failed);
                throw;
            }
            (context.getState()).Entry(context);
        }

        return;
    }

    void XbeInstdFSM_Shutdown::Entry(XbeInstdContext& context)

{
        XbeInstd& ctxt(context.getOwner());

        ctxt.do_stop_lifesign();
        ctxt.do_stop_timer();
        return;
    }

    void XbeInstdFSM_Shutdown::LifeSign(XbeInstdContext& context)
    {


        return;
    }

    void XbeInstdFSM_Shutdown::StatusReq(XbeInstdContext& context, xbe::event::StatusReqEvent& msg)
    {


        return;
    }

    void XbeInstdFSM_Failed::Entry(XbeInstdContext& context)

{
        XbeInstd& ctxt(context.getOwner());

        ctxt.do_stop_lifesign();
        ctxt.do_stop_timer();
        return;
    }

    void XbeInstdFSM_Failed::LifeSign(XbeInstdContext& context)
    {


        return;
    }

    void XbeInstdFSM_Failed::StatusReq(XbeInstdContext& context, xbe::event::StatusReqEvent& msg)
    {


        return;
    }
}

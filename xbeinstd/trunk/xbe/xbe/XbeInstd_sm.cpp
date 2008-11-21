
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
#include "XbeInstd.hpp"
#include "XbeInstd_sm.h"

using namespace statemap;

namespace xbe
{
    // Static class declarations.
    XbeInstdFSM_Idle XbeInstdFSM::Idle("XbeInstdFSM::Idle", 0);
    XbeInstdFSM_Busy XbeInstdFSM::Busy("XbeInstdFSM::Busy", 1);
    XbeInstdFSM_WaitForFinishedAck XbeInstdFSM::WaitForFinishedAck("XbeInstdFSM::WaitForFinishedAck", 2);
    XbeInstdFSM_Shutdown XbeInstdFSM::Shutdown("XbeInstdFSM::Shutdown", 3);
    XbeInstdFSM_Failed XbeInstdFSM::Failed("XbeInstdFSM::Failed", 4);

    void XbeInstdState::Execute(XbeInstdContext& context, xbe::event::ExecuteEvent& msg)
    {
        Default(context);
        return;
    }

    void XbeInstdState::Finished(XbeInstdContext& context)
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

    void XbeInstdState::StatusReq(XbeInstdContext& context, xbe::event::StatusReqEvent& msg)
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

    void XbeInstdFSM_Default::StatusReq(XbeInstdContext& context, xbe::event::StatusReqEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        XbeInstdState& EndStateName = context.getState();

        context.clearState();
        try
        {
            ctxt.do_send_status(msg);
            context.setState(EndStateName);
        }
        catch (...)
        {
            context.setState(EndStateName);
            throw;
        }

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

    void XbeInstdFSM_Idle::Execute(XbeInstdContext& context, xbe::event::ExecuteEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        (context.getState()).Exit(context);
        context.clearState();
        try
        {
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

    void XbeInstdFSM_Idle::Terminate(XbeInstdContext& context, xbe::event::TerminateEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        XbeInstdState& EndStateName = context.getState();

        context.clearState();
        try
        {
            ctxt.do_terminate(msg);
            context.setState(EndStateName);
        }
        catch (...)
        {
            context.setState(EndStateName);
            throw;
        }

        return;
    }

    void XbeInstdFSM_Busy::Finished(XbeInstdContext& context)
    {
        XbeInstd& ctxt(context.getOwner());

        (context.getState()).Exit(context);
        context.clearState();
        try
        {
            ctxt.do_task_finished();
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
            ctxt.do_terminate_job();
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

    void XbeInstdFSM_Busy::Terminate(XbeInstdContext& context, xbe::event::TerminateEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        (context.getState()).Exit(context);
        context.clearState();
        try
        {
            ctxt.do_terminate_job();
            ctxt.do_terminate(msg);
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

    void XbeInstdFSM_WaitForFinishedAck::FinishedAck(XbeInstdContext& context, xbe::event::FinishedAckEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        (context.getState()).Exit(context);
        context.clearState();
        try
        {
            ctxt.do_stop_timer();
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

    void XbeInstdFSM_WaitForFinishedAck::Terminate(XbeInstdContext& context, xbe::event::TerminateEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        (context.getState()).Exit(context);
        context.clearState();
        try
        {
            ctxt.do_terminate(msg);
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

    void XbeInstdFSM_WaitForFinishedAck::Timeout(XbeInstdContext& context)
    {
        XbeInstd& ctxt(context.getOwner());

        if (ctxt.retryCounter() < ctxt.maxRetries())
        {
            XbeInstdState& EndStateName = context.getState();

            context.clearState();
            try
            {
                ctxt.do_task_finished();
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

    void XbeInstdFSM_Shutdown::LifeSign(XbeInstdContext& context)
    {


        return;
    }

    void XbeInstdFSM_Failed::LifeSign(XbeInstdContext& context)
    {


        return;
    }
}

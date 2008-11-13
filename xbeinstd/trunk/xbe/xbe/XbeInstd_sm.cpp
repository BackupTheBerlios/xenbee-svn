
//
// Finite state machine for the XbeInstd
//


#include <xbe/event/ExecuteEvent.hpp>
#include <xbe/event/LifeSignEvent.hpp>
#include <xbe/event/StatusReqEvent.hpp>
#include <xbe/event/TerminateEvent.hpp>
#include <xbe/event/FinishedEvent.hpp>
#include <xbe/event/FailedEvent.hpp>
#include "XbeInstd.hpp"
#include "XbeInstd_sm.h"

using namespace statemap;

namespace xbe
{
    // Static class declarations.
    XbeInstdFSM_Idle XbeInstdFSM::Idle("XbeInstdFSM::Idle", 0);
    XbeInstdFSM_Executing XbeInstdFSM::Executing("XbeInstdFSM::Executing", 1);
    XbeInstdFSM_Terminated XbeInstdFSM::Terminated("XbeInstdFSM::Terminated", 2);

    void XbeInstdState::Execute(XbeInstdContext& context, const xbe::event::ExecuteEvent& msg)
    {
        Default(context);
        return;
    }

    void XbeInstdState::Failed(XbeInstdContext& context, const xbe::event::FailedEvent& msg)
    {
        Default(context);
        return;
    }

    void XbeInstdState::Finished(XbeInstdContext& context, const xbe::event::FinishedEvent& msg)
    {
        Default(context);
        return;
    }

    void XbeInstdState::LifeSign(XbeInstdContext& context, const xbe::event::LifeSignEvent& msg)
    {
        Default(context);
        return;
    }

    void XbeInstdState::StatusReq(XbeInstdContext& context, const xbe::event::StatusReqEvent& msg)
    {
        Default(context);
        return;
    }

    void XbeInstdState::Terminate(XbeInstdContext& context, const xbe::event::TerminateEvent& msg)
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

    void XbeInstdFSM_Idle::Execute(XbeInstdContext& context, const xbe::event::ExecuteEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        (context.getState()).Exit(context);
        context.clearState();
        try
        {
            ctxt.do_execute(msg);
            context.setState(XbeInstdFSM::Executing);
        }
        catch (...)
        {
            context.setState(XbeInstdFSM::Executing);
            throw;
        }
        (context.getState()).Entry(context);

        return;
    }

    void XbeInstdFSM_Idle::LifeSign(XbeInstdContext& context, const xbe::event::LifeSignEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        XbeInstdState& EndStateName = context.getState();

        context.clearState();
        try
        {
            ctxt.do_send_lifesign(msg);
            context.setState(EndStateName);
        }
        catch (...)
        {
            context.setState(EndStateName);
            throw;
        }

        return;
    }

    void XbeInstdFSM_Idle::StatusReq(XbeInstdContext& context, const xbe::event::StatusReqEvent& msg)
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

    void XbeInstdFSM_Idle::Terminate(XbeInstdContext& context, const xbe::event::TerminateEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        (context.getState()).Exit(context);
        context.clearState();
        try
        {
            ctxt.do_terminate(msg);
            context.setState(XbeInstdFSM::Terminated);
        }
        catch (...)
        {
            context.setState(XbeInstdFSM::Terminated);
            throw;
        }
        (context.getState()).Entry(context);

        return;
    }

    void XbeInstdFSM_Executing::Failed(XbeInstdContext& context, const xbe::event::FailedEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        (context.getState()).Exit(context);
        context.clearState();
        try
        {
            ctxt.do_failed(msg);
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

    void XbeInstdFSM_Executing::Finished(XbeInstdContext& context, const xbe::event::FinishedEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        (context.getState()).Exit(context);
        context.clearState();
        try
        {
            ctxt.do_finished(msg);
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

    void XbeInstdFSM_Executing::LifeSign(XbeInstdContext& context, const xbe::event::LifeSignEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        XbeInstdState& EndStateName = context.getState();

        context.clearState();
        try
        {
            ctxt.do_send_lifesign(msg);
            context.setState(EndStateName);
        }
        catch (...)
        {
            context.setState(EndStateName);
            throw;
        }

        return;
    }

    void XbeInstdFSM_Executing::StatusReq(XbeInstdContext& context, const xbe::event::StatusReqEvent& msg)
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

    void XbeInstdFSM_Executing::Terminate(XbeInstdContext& context, const xbe::event::TerminateEvent& msg)
    {
        XbeInstd& ctxt(context.getOwner());

        (context.getState()).Exit(context);
        context.clearState();
        try
        {
            ctxt.do_terminate_job();
            ctxt.do_terminate(msg);
            context.setState(XbeInstdFSM::Terminated);
        }
        catch (...)
        {
            context.setState(XbeInstdFSM::Terminated);
            throw;
        }
        (context.getState()).Entry(context);

        return;
    }
}

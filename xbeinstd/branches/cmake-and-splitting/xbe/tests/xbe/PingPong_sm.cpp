
//
// Copyright (c) 2008 Fraunhofer ITWM
// Alexander Petry <petry@itmw.fhg.de>
//
// Finite state machine for the MessagePingPongTest
//


#include <tests/xbe/PingEvent.hpp>
#include <tests/xbe/PongEvent.hpp>
#include "PingPong.hpp"
#include "PingPong_sm.h"

using namespace statemap;

namespace tests
{
    namespace xbe
    {
        // Static class declarations.
        PingPongFSM_Idle PingPongFSM::Idle("PingPongFSM::Idle", 0);
        PingPongFSM_Active PingPongFSM::Active("PingPongFSM::Active", 1);

        void PingPongState::Ping(PingPongContext& context, const tests::xbe::PingEvent& msg)
        {
            Default(context);
            return;
        }

        void PingPongState::Pong(PingPongContext& context, const tests::xbe::PongEvent& msg)
        {
            Default(context);
            return;
        }

        void PingPongState::Start(PingPongContext& context)
        {
            Default(context);
            return;
        }

        void PingPongState::Stop(PingPongContext& context)
        {
            Default(context);
            return;
        }

        void PingPongState::Default(PingPongContext& context)
        {
            throw (
                TransitionUndefinedException(
                    context.getState().getName(),
                    context.getTransition()));

            return;
        }

        void PingPongFSM_Idle::Ping(PingPongContext& context, const tests::xbe::PingEvent& msg)
        {


            return;
        }

        void PingPongFSM_Idle::Pong(PingPongContext& context, const tests::xbe::PongEvent& msg)
        {


            return;
        }

        void PingPongFSM_Idle::Start(PingPongContext& context)
        {
            PingPong& ctxt(context.getOwner());

            (context.getState()).Exit(context);
            context.clearState();
            try
            {
                ctxt.start();
                context.setState(PingPongFSM::Active);
            }
            catch (...)
            {
                context.setState(PingPongFSM::Active);
                throw;
            }
            (context.getState()).Entry(context);

            return;
        }

        void PingPongFSM_Idle::Stop(PingPongContext& context)
        {


            return;
        }

        void PingPongFSM_Active::Ping(PingPongContext& context, const tests::xbe::PingEvent& msg)
        {
            PingPong& ctxt(context.getOwner());

            PingPongState& EndStateName = context.getState();

            context.clearState();
            try
            {
                ctxt.sendPong(msg);
                context.setState(EndStateName);
            }
            catch (...)
            {
                context.setState(EndStateName);
                throw;
            }

            return;
        }

        void PingPongFSM_Active::Pong(PingPongContext& context, const tests::xbe::PongEvent& msg)
        {
            PingPong& ctxt(context.getOwner());

            PingPongState& EndStateName = context.getState();

            context.clearState();
            try
            {
                ctxt.sendPing(msg);
                context.setState(EndStateName);
            }
            catch (...)
            {
                context.setState(EndStateName);
                throw;
            }

            return;
        }

        void PingPongFSM_Active::Start(PingPongContext& context)
        {


            return;
        }

        void PingPongFSM_Active::Stop(PingPongContext& context)
        {
            PingPong& ctxt(context.getOwner());

            (context.getState()).Exit(context);
            context.clearState();
            try
            {
                ctxt.stop();
                context.setState(PingPongFSM::Idle);
            }
            catch (...)
            {
                context.setState(PingPongFSM::Idle);
                throw;
            }
            (context.getState()).Entry(context);

            return;
        }
    }
}

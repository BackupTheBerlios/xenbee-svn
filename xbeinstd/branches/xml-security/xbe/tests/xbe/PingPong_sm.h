#ifndef _H_PINGPONG_SM
#define _H_PINGPONG_SM

#define SMC_USES_IOSTREAMS

#include <statemap.h>

namespace tests
{
    namespace xbe
    {
        // Forward declarations.
        class PingPongFSM;
        class PingPongFSM_Idle;
        class PingPongFSM_Active;
        class PingPongFSM_Default;
        class PingPongState;
        class PingPongContext;
        class PingPong;

        class PingPongState :
            public statemap::State
        {
        public:

            PingPongState(const char *name, int stateId)
            : statemap::State(name, stateId)
            {};

            virtual void Entry(PingPongContext&) {};
            virtual void Exit(PingPongContext&) {};

            virtual void Ping(PingPongContext& context, const tests::xbe::PingEvent& msg);
            virtual void Pong(PingPongContext& context, const tests::xbe::PongEvent& msg);
            virtual void Start(PingPongContext& context);
            virtual void Stop(PingPongContext& context);

        protected:

            virtual void Default(PingPongContext& context);
        };

        class PingPongFSM
        {
        public:

            static PingPongFSM_Idle Idle;
            static PingPongFSM_Active Active;
        };

        class PingPongFSM_Default :
            public PingPongState
        {
        public:

            PingPongFSM_Default(const char *name, int stateId)
            : PingPongState(name, stateId)
            {};

        };

        class PingPongFSM_Idle :
            public PingPongFSM_Default
        {
        public:
            PingPongFSM_Idle(const char *name, int stateId)
            : PingPongFSM_Default(name, stateId)
            {};

            void Ping(PingPongContext& context, const tests::xbe::PingEvent& msg);
            void Pong(PingPongContext& context, const tests::xbe::PongEvent& msg);
            void Start(PingPongContext& context);
            void Stop(PingPongContext& context);
        };

        class PingPongFSM_Active :
            public PingPongFSM_Default
        {
        public:
            PingPongFSM_Active(const char *name, int stateId)
            : PingPongFSM_Default(name, stateId)
            {};

            void Ping(PingPongContext& context, const tests::xbe::PingEvent& msg);
            void Pong(PingPongContext& context, const tests::xbe::PongEvent& msg);
            void Start(PingPongContext& context);
            void Stop(PingPongContext& context);
        };

        class PingPongContext :
            public statemap::FSMContext
        {
        public:

            PingPongContext(PingPong& owner)
            : _owner(owner)
            {
                setState(PingPongFSM::Idle);
                PingPongFSM::Idle.Entry(*this);
            };

            PingPong& getOwner() const
            {
                return (_owner);
            };

            PingPongState& getState() const
            {
                if (_state == NULL)
                {
                    throw statemap::StateUndefinedException();
                }

                return (dynamic_cast<PingPongState&>(*_state));
            };

            void Ping(const tests::xbe::PingEvent& msg)
            {
                (getState()).Ping(*this, msg);
            };

            void Pong(const tests::xbe::PongEvent& msg)
            {
                (getState()).Pong(*this, msg);
            };

            void Start()
            {
                (getState()).Start(*this);
            };

            void Stop()
            {
                (getState()).Stop(*this);
            };

        private:

            PingPong& _owner;
        };
    };

};

#endif

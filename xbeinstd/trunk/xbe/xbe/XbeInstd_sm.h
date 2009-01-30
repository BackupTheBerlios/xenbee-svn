#ifndef _H_XBEINSTD_SM
#define _H_XBEINSTD_SM

#define SMC_USES_IOSTREAMS

#include <statemap.h>

namespace xbe
{
    // Forward declarations.
    class XbeInstdFSM;
    class XbeInstdFSM_Init;
    class XbeInstdFSM_Idle;
    class XbeInstdFSM_Busy;
    class XbeInstdFSM_WaitForTaskTermination;
    class XbeInstdFSM_WaitForFinishedAck;
    class XbeInstdFSM_Shutdown;
    class XbeInstdFSM_Failed;
    class XbeInstdFSM_Default;
    class XbeInstdState;
    class XbeInstdContext;
    class XbeInstd;

    class XbeInstdState :
        public statemap::State
    {
    public:

        XbeInstdState(const char *name, int stateId)
        : statemap::State(name, stateId)
        {};

        virtual void Entry(XbeInstdContext&) {};
        virtual void Exit(XbeInstdContext&) {};

        virtual void Execute(XbeInstdContext& context, xbe::event::ExecuteEvent& msg);
        virtual void Finished(XbeInstdContext& context);
        virtual void FinishedAck(XbeInstdContext& context, xbe::event::FinishedAckEvent& msg);
        virtual void LifeSign(XbeInstdContext& context);
        virtual void Shutdown(XbeInstdContext& context, xbe::event::ShutdownEvent& msg);
        virtual void Start(XbeInstdContext& context);
        virtual void StatusReq(XbeInstdContext& context, xbe::event::StatusReqEvent& msg);
        virtual void Terminate(XbeInstdContext& context);
        virtual void Terminate(XbeInstdContext& context, xbe::event::TerminateEvent& msg);
        virtual void Timeout(XbeInstdContext& context);

    protected:

        virtual void Default(XbeInstdContext& context);
    };

    class XbeInstdFSM
    {
    public:

        static XbeInstdFSM_Init Init;
        static XbeInstdFSM_Idle Idle;
        static XbeInstdFSM_Busy Busy;
        static XbeInstdFSM_WaitForTaskTermination WaitForTaskTermination;
        static XbeInstdFSM_WaitForFinishedAck WaitForFinishedAck;
        static XbeInstdFSM_Shutdown Shutdown;
        static XbeInstdFSM_Failed Failed;
    };

    class XbeInstdFSM_Default :
        public XbeInstdState
    {
    public:

        XbeInstdFSM_Default(const char *name, int stateId)
        : XbeInstdState(name, stateId)
        {};

        virtual void Execute(XbeInstdContext& context, xbe::event::ExecuteEvent& msg);
        virtual void StatusReq(XbeInstdContext& context, xbe::event::StatusReqEvent& msg);
        virtual void LifeSign(XbeInstdContext& context);
    };

    class XbeInstdFSM_Init :
        public XbeInstdFSM_Default
    {
    public:
        XbeInstdFSM_Init(const char *name, int stateId)
        : XbeInstdFSM_Default(name, stateId)
        {};

        void Start(XbeInstdContext& context);
    };

    class XbeInstdFSM_Idle :
        public XbeInstdFSM_Default
    {
    public:
        XbeInstdFSM_Idle(const char *name, int stateId)
        : XbeInstdFSM_Default(name, stateId)
        {};

        void Execute(XbeInstdContext& context, xbe::event::ExecuteEvent& msg);
        void Finished(XbeInstdContext& context);
        void FinishedAck(XbeInstdContext& context, xbe::event::FinishedAckEvent& msg);
        void Shutdown(XbeInstdContext& context, xbe::event::ShutdownEvent& msg);
        void Terminate(XbeInstdContext& context, xbe::event::TerminateEvent& msg);
    };

    class XbeInstdFSM_Busy :
        public XbeInstdFSM_Default
    {
    public:
        XbeInstdFSM_Busy(const char *name, int stateId)
        : XbeInstdFSM_Default(name, stateId)
        {};

        void Execute(XbeInstdContext& context, xbe::event::ExecuteEvent& msg);
        void Finished(XbeInstdContext& context);
        void Shutdown(XbeInstdContext& context, xbe::event::ShutdownEvent& msg);
        void Terminate(XbeInstdContext& context, xbe::event::TerminateEvent& msg);
    };

    class XbeInstdFSM_WaitForTaskTermination :
        public XbeInstdFSM_Default
    {
    public:
        XbeInstdFSM_WaitForTaskTermination(const char *name, int stateId)
        : XbeInstdFSM_Default(name, stateId)
        {};

        void Entry(XbeInstdContext&);
        void Exit(XbeInstdContext&);
        void Finished(XbeInstdContext& context);
        void Terminate(XbeInstdContext& context);
        void Timeout(XbeInstdContext& context);
    };

    class XbeInstdFSM_WaitForFinishedAck :
        public XbeInstdFSM_Default
    {
    public:
        XbeInstdFSM_WaitForFinishedAck(const char *name, int stateId)
        : XbeInstdFSM_Default(name, stateId)
        {};

        void Entry(XbeInstdContext&);
        void Exit(XbeInstdContext&);
        void FinishedAck(XbeInstdContext& context, xbe::event::FinishedAckEvent& msg);
        void Shutdown(XbeInstdContext& context, xbe::event::ShutdownEvent& msg);
        void Terminate(XbeInstdContext& context, xbe::event::TerminateEvent& msg);
        void Timeout(XbeInstdContext& context);
    };

    class XbeInstdFSM_Shutdown :
        public XbeInstdFSM_Default
    {
    public:
        XbeInstdFSM_Shutdown(const char *name, int stateId)
        : XbeInstdFSM_Default(name, stateId)
        {};

        void Entry(XbeInstdContext&);
        void LifeSign(XbeInstdContext& context);
        void StatusReq(XbeInstdContext& context, xbe::event::StatusReqEvent& msg);
    };

    class XbeInstdFSM_Failed :
        public XbeInstdFSM_Default
    {
    public:
        XbeInstdFSM_Failed(const char *name, int stateId)
        : XbeInstdFSM_Default(name, stateId)
        {};

        void Entry(XbeInstdContext&);
        void LifeSign(XbeInstdContext& context);
        void StatusReq(XbeInstdContext& context, xbe::event::StatusReqEvent& msg);
    };

    class XbeInstdContext :
        public statemap::FSMContext
    {
    public:

        XbeInstdContext(XbeInstd& owner)
        : _owner(owner)
        {
            setState(XbeInstdFSM::Init);
            XbeInstdFSM::Init.Entry(*this);
        };

        XbeInstd& getOwner() const
        {
            return (_owner);
        };

        XbeInstdState& getState() const
        {
            if (_state == NULL)
            {
                throw statemap::StateUndefinedException();
            }

            return (dynamic_cast<XbeInstdState&>(*_state));
        };

        void Execute(xbe::event::ExecuteEvent& msg)
        {
            (getState()).Execute(*this, msg);
        };

        void Finished()
        {
            (getState()).Finished(*this);
        };

        void FinishedAck(xbe::event::FinishedAckEvent& msg)
        {
            (getState()).FinishedAck(*this, msg);
        };

        void LifeSign()
        {
            (getState()).LifeSign(*this);
        };

        void Shutdown(xbe::event::ShutdownEvent& msg)
        {
            (getState()).Shutdown(*this, msg);
        };

        void Start()
        {
            (getState()).Start(*this);
        };

        void StatusReq(xbe::event::StatusReqEvent& msg)
        {
            (getState()).StatusReq(*this, msg);
        };

        void Terminate()
        {
            (getState()).Terminate(*this);
        };

        void Terminate(xbe::event::TerminateEvent& msg)
        {
            (getState()).Terminate(*this, msg);
        };

        void Timeout()
        {
            (getState()).Timeout(*this);
        };

    private:

        XbeInstd& _owner;
    };
}

#endif // _H_XBEINSTD_SM

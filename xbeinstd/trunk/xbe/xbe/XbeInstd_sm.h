#ifndef _H_XBEINSTD_SM
#define _H_XBEINSTD_SM

#define SMC_USES_IOSTREAMS

#include <statemap.h>

namespace xbe
{
    // Forward declarations.
    class XbeInstdFSM;
    class XbeInstdFSM_Idle;
    class XbeInstdFSM_Executing;
    class XbeInstdFSM_Terminated;
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

        virtual void Execute(XbeInstdContext& context, const xbe::ExecuteEvent& msg);
        virtual void Failed(XbeInstdContext& context, const xbe::FailedEvent& msg);
        virtual void Finished(XbeInstdContext& context, const xbe::FinishedEvent& msg);
        virtual void LifeSign(XbeInstdContext& context, const xbe::LifeSignEvent& msg);
        virtual void StatusReq(XbeInstdContext& context, const xbe::StatusReqEvent& msg);
        virtual void Terminate(XbeInstdContext& context, const xbe::TerminateEvent& msg);

    protected:

        virtual void Default(XbeInstdContext& context);
    };

    class XbeInstdFSM
    {
    public:

        static XbeInstdFSM_Idle Idle;
        static XbeInstdFSM_Executing Executing;
        static XbeInstdFSM_Terminated Terminated;
    };

    class XbeInstdFSM_Default :
        public XbeInstdState
    {
    public:

        XbeInstdFSM_Default(const char *name, int stateId)
        : XbeInstdState(name, stateId)
        {};

    };

    class XbeInstdFSM_Idle :
        public XbeInstdFSM_Default
    {
    public:
        XbeInstdFSM_Idle(const char *name, int stateId)
        : XbeInstdFSM_Default(name, stateId)
        {};

        void Execute(XbeInstdContext& context, const xbe::ExecuteEvent& msg);
        void LifeSign(XbeInstdContext& context, const xbe::LifeSignEvent& msg);
        void StatusReq(XbeInstdContext& context, const xbe::StatusReqEvent& msg);
        void Terminate(XbeInstdContext& context, const xbe::TerminateEvent& msg);
    };

    class XbeInstdFSM_Executing :
        public XbeInstdFSM_Default
    {
    public:
        XbeInstdFSM_Executing(const char *name, int stateId)
        : XbeInstdFSM_Default(name, stateId)
        {};

        void Failed(XbeInstdContext& context, const xbe::FailedEvent& msg);
        void Finished(XbeInstdContext& context, const xbe::FinishedEvent& msg);
        void LifeSign(XbeInstdContext& context, const xbe::LifeSignEvent& msg);
        void StatusReq(XbeInstdContext& context, const xbe::StatusReqEvent& msg);
        void Terminate(XbeInstdContext& context, const xbe::TerminateEvent& msg);
    };

    class XbeInstdFSM_Terminated :
        public XbeInstdFSM_Default
    {
    public:
        XbeInstdFSM_Terminated(const char *name, int stateId)
        : XbeInstdFSM_Default(name, stateId)
        {};

    };

    class XbeInstdContext :
        public statemap::FSMContext
    {
    public:

        XbeInstdContext(XbeInstd& owner)
        : _owner(owner)
        {
            setState(XbeInstdFSM::Idle);
            XbeInstdFSM::Idle.Entry(*this);
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

        void Execute(const xbe::ExecuteEvent& msg)
        {
            (getState()).Execute(*this, msg);
        };

        void Failed(const xbe::FailedEvent& msg)
        {
            (getState()).Failed(*this, msg);
        };

        void Finished(const xbe::FinishedEvent& msg)
        {
            (getState()).Finished(*this, msg);
        };

        void LifeSign(const xbe::LifeSignEvent& msg)
        {
            (getState()).LifeSign(*this, msg);
        };

        void StatusReq(const xbe::StatusReqEvent& msg)
        {
            (getState()).StatusReq(*this, msg);
        };

        void Terminate(const xbe::TerminateEvent& msg)
        {
            (getState()).Terminate(*this, msg);
        };

    private:

        XbeInstd& _owner;
    };
}

#endif // _H_XBEINSTD_SM

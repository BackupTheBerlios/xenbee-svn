#ifndef _H_TASK_SM
#define _H_TASK_SM

#define SMC_USES_IOSTREAMS

#include <statemap.h>

namespace xbe
{
    // Forward declarations.
    class TaskFSM;
    class TaskFSM_Idle;
    class TaskFSM_Executing;
    class TaskFSM_Terminated;
    class TaskFSM_Failed;
    class TaskFSM_Finished;
    class TaskFSM_Default;
    class TaskState;
    class TaskContext;
    class Task;

    class TaskState :
        public statemap::State
    {
    public:

        TaskState(const char *name, int stateId)
        : statemap::State(name, stateId)
        {};

        virtual void Entry(TaskContext&) {};
        virtual void Exit(TaskContext&) {};


    protected:

        virtual void Default(TaskContext& context);
    };

    class TaskFSM
    {
    public:

        static TaskFSM_Idle Idle;
        static TaskFSM_Executing Executing;
        static TaskFSM_Terminated Terminated;
        static TaskFSM_Failed Failed;
        static TaskFSM_Finished Finished;
    };

    class TaskFSM_Default :
        public TaskState
    {
    public:

        TaskFSM_Default(const char *name, int stateId)
        : TaskState(name, stateId)
        {};

    };

    class TaskFSM_Idle :
        public TaskFSM_Default
    {
    public:
        TaskFSM_Idle(const char *name, int stateId)
        : TaskFSM_Default(name, stateId)
        {};

    };

    class TaskFSM_Executing :
        public TaskFSM_Default
    {
    public:
        TaskFSM_Executing(const char *name, int stateId)
        : TaskFSM_Default(name, stateId)
        {};

    };

    class TaskFSM_Terminated :
        public TaskFSM_Default
    {
    public:
        TaskFSM_Terminated(const char *name, int stateId)
        : TaskFSM_Default(name, stateId)
        {};

    };

    class TaskFSM_Failed :
        public TaskFSM_Default
    {
    public:
        TaskFSM_Failed(const char *name, int stateId)
        : TaskFSM_Default(name, stateId)
        {};

    };

    class TaskFSM_Finished :
        public TaskFSM_Default
    {
    public:
        TaskFSM_Finished(const char *name, int stateId)
        : TaskFSM_Default(name, stateId)
        {};

    };

    class TaskContext :
        public statemap::FSMContext
    {
    public:

        TaskContext(Task& owner)
        : _owner(owner)
        {
            setState(TaskFSM::Idle);
            TaskFSM::Idle.Entry(*this);
        };

        Task& getOwner() const
        {
            return (_owner);
        };

        TaskState& getState() const
        {
            if (_state == NULL)
            {
                throw statemap::StateUndefinedException();
            }

            return (dynamic_cast<TaskState&>(*_state));
        };

    private:

        Task& _owner;
    };
}

#endif // _H_TASK_SM

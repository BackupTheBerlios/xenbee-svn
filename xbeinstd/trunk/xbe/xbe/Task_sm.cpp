
//
// Finite state machine for the XbeInstd Task
//


#include "Task.hpp"
#include "Task_sm.h"

using namespace statemap;

namespace xbe
{
    // Static class declarations.
    TaskFSM_Idle TaskFSM::Idle("TaskFSM::Idle", 0);
    TaskFSM_Executing TaskFSM::Executing("TaskFSM::Executing", 1);
    TaskFSM_Terminated TaskFSM::Terminated("TaskFSM::Terminated", 2);
    TaskFSM_Failed TaskFSM::Failed("TaskFSM::Failed", 3);
    TaskFSM_Finished TaskFSM::Finished("TaskFSM::Finished", 4);

    void TaskState::Default(TaskContext& context)
    {
        throw (
            TransitionUndefinedException(
                context.getState().getName(),
                context.getTransition()));

        return;
    }
}

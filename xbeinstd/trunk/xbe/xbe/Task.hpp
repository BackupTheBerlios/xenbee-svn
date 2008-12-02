#ifndef XBE_TASK_HPP
#define XBE_TASK_HPP 1

#include <xbe/common.hpp>
#include <xbe/TaskData.hpp>

#include <string>
#include <list>
#include <map>

#include <sys/types.h>
#include <unistd.h>

#include <boost/filesystem.hpp>
#include <boost/thread.hpp>

namespace xbe {
    class Task;
    class TaskListener {
        public:
            virtual void onTaskExit(const Task *) = 0;
            virtual void onTaskFailure(const Task *) = 0;
    };

    class Task {
        public:
            enum Status {
                UNKNOWN,
                FINISHED,
                SIGNALED,
                FAILED
            };

            explicit Task(const TaskData &td);

            virtual ~Task();
            
            /**
             * Executes the given task by calling the fork / exec pair of
             * syscalls. If "fork" was successful, the pid is remembered
             * otherwise an exception is thrown. The status of the subsequent
             * "exec" can only be retrieved by querying the status.
             */
            void run();

            /* waits until the subprocess has finished */
            void wait();

            void wait(const boost::posix_time::time_duration &timeout);

            /* thread entry function that observes the created sub process */
            void operator()();

            const TaskData& taskData() const { return _taskData; }
            TaskData& taskData() { return _taskData; }

            pid_t pid() const { return _pid; }
            int exitcode() const { return _exitCode; }
            Status status() const { return _status; }
            int kill(int signal);
            bool running();

            void setTaskListener(TaskListener *taskListener) { _taskListener = taskListener; }
        private:
            char** build_argv() const;
            char** build_envp() const;

            XBE_DECLARE_LOGGER();

            TaskData _taskData;

            int _exitCode;
            Status _status;
            pid_t _pid;
            TaskListener *_taskListener;
            boost::thread _thread;
            boost::barrier _barrier;
            boost::recursive_mutex _mtx;
            boost::condition_variable_any _cond;
    };
}

#endif // ! XBE_TASK_HPP

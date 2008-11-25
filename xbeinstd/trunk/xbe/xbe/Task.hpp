#ifndef XBE_TASK_HPP
#define XBE_TASK_HPP 1

#include <xbe/common.hpp>

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

            enum RedirectType {
                NONE,
                CLOSE,
                FILE,
                PIPE
            };

            typedef std::map<std::string, std::string> env_t;
            typedef std::vector<std::string> params_t;

            explicit Task(const boost::filesystem::path &path);

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

            /* thread entry function that observes the created sub process */
            void operator()();

            const env_t & env() const { return _env; }
            env_t & env() { return _env; }

            const params_t & params() const { return _params; }
            params_t & params() { return _params; }

            const std::string & path() const { return _params.front(); }

            const boost::filesystem::path & wd() const { return _workingDir; }
            boost::filesystem::path & wd() { return _workingDir; }

            const uid_t & uid() const { return _uid; }
            uid_t & uid() { return _uid; }

            const gid_t & gid() const { return _gid; }
            gid_t & gid() { return _gid; }

            /* The following three functions act as follows:
             *
             * If redirect-type is:
             *  NONE: the stream of the created child is left untouched
             *  CLOSE: the stream is closed
             *  FILE: the given path is opened and the file descriptor is passed to the child
             *  PIPE: a pipe will be created and can be used to write to/read from the child
             *
             */
            void redirect_stdin(const boost::filesystem::path &path)  { _pathStdin = path; }   //, RedirectType rtype);
            void redirect_stdout(const boost::filesystem::path &path) { _pathStdout = path; } //, RedirectType rtype);
            void redirect_stderr(const boost::filesystem::path &path) { _pathStderr = path; } //, RedirectType rtype);

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

            boost::filesystem::path _path;
            boost::filesystem::path _workingDir;

            boost::filesystem::path _pathStdin;
            boost::filesystem::path _pathStdout;
            boost::filesystem::path _pathStderr;

            params_t _params;
            env_t _env;
            uid_t _uid;
            gid_t _gid;
            pid_t _pid;
            int _exitCode;
            Status _status;
            TaskListener *_taskListener;
            boost::thread _thread;
            boost::barrier _barrier;
            boost::recursive_mutex _mtx;
            boost::condition_variable_any _cond;
    };
}

#endif // ! XBE_TASK_HPP

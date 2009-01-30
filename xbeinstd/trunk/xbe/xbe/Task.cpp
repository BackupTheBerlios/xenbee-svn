#include "Task.hpp"

#include <unistd.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/wait.h>
#include <signal.h>

using namespace xbe;

Task::Task(const TaskData &td)
    : XBE_INIT_LOGGER("xbe.task:"+td.path()), _taskData(td),
    _pid(0), _status(UNKNOWN), _exitCode(0), _taskListener(0), _barrier(2)
{}

Task::~Task() {
    _taskListener=NULL;
    if (running()) {
        kill(SIGKILL);
    }
}

void Task::operator()() {
    // wait until the sub process has been started
    // observe the created sub processes from within a thread.
    _barrier.wait();
    if (pid() > 0) {
        waitpid(pid(), &_exitCode, 0);
        XBE_LOG_DEBUG("task finished");
        {
            boost::unique_lock<boost::recursive_mutex> lock(_mtx);
            if (WIFEXITED(_exitCode)) {
                _status = FINISHED;
                _exitCode = WEXITSTATUS(_exitCode);
            } else if (WIFSIGNALED(_exitCode)) {
                _status = SIGNALED;
                _exitCode = WTERMSIG(_exitCode);
            } else {
                _status = FAILED;
            }
        }

        if (_taskListener) {
            _taskListener->onTaskExit(this);
        }
    } else if (pid() < 0) {
        XBE_LOG_DEBUG("task failed");
        {
            boost::unique_lock<boost::recursive_mutex> lock(_mtx);
            _status = FAILED;
            _exitCode = errno;
        }

        if (_taskListener) {
            _taskListener->onTaskFailure(this);
        }
    }
    _thread.detach();
    _cond.notify_one();
}

void Task::wait() {
    XBE_LOG_DEBUG("waiting for subprocess to finish");
    boost::unique_lock<boost::recursive_mutex> lock(_mtx);
    if (running()) {
        while (status() == UNKNOWN )
            _cond.wait(lock);
    }
}

void Task::wait(const boost::posix_time::time_duration &timeout) {
    boost::unique_lock<boost::recursive_mutex> lock(_mtx);
    if (running()) {
        if (status() == UNKNOWN )
            _cond.timed_wait(lock, timeout);
    }
}


int Task::kill(int signal) {
    boost::unique_lock<boost::recursive_mutex> lock(_mtx);
    if (status() == UNKNOWN && running()) {
        return ::kill(pid(), signal);
    }
}

bool Task::running() {
    boost::unique_lock<boost::recursive_mutex> lock(_mtx);
    return (_thread.get_id() != boost::thread::id());
}

void Task::run() {
    boost::unique_lock<boost::recursive_mutex> lock(_mtx);
    // no active thread
    if (! running()) {
        _status = UNKNOWN;
        _exitCode = 0;

        // no thread running, create it
        _thread = boost::thread(boost::ref(*this));

        XBE_LOG_DEBUG("forking");

        _pid = fork();
        if (_pid == 0) {
            // close open file descriptors
            for (int fd = 0; fd < 1024; fd++)
                close(fd);
            // redirect stdin stdout stderr
            if (!_taskData.stdIn().empty()) {
                int fd = open(_taskData.stdIn().c_str(), O_RDONLY);
                dup2(fd, 0);
            }
            if (!_taskData.stdOut().empty()) {
                int fd = open(_taskData.stdOut().c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0600);
                dup2(fd, 1);
            }
            if (!_taskData.stdErr().empty()) {
                int fd = open(_taskData.stdErr().c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0600);
                dup2(fd, 2);
            }

            // set uid, gid
            setuid(_taskData.uid());
            setgid(_taskData.gid());

            // set working directory
            chdir(_taskData.wd().string().c_str());

            // build argv and envp
            char **argv = build_argv();
            char **envp = build_envp();

            // child process, perform exec
            if (execve(argv[0], argv, envp) < 0) {
                // exec failed
                exit(127);
            }
        } else {
            _barrier.wait();
        }
    } else {
        // thread is already running...
        XBE_LOG_INFO("task already running!");
    }
}

char **Task::build_argv() const {
    const size_t numParams(_taskData.params().size());
    char **argv = new char*[numParams + 1];

    for (std::size_t i = 0; i < numParams; i++) {
        const std::string::size_type len(_taskData.params()[i].size());

        argv[i] = new char[len+1];
        strncpy(argv[i], _taskData.params()[i].c_str(), len);
        argv[i][len] = (char)0;
    }
    argv[numParams] = (char*)0;
    return argv;
}

char **Task::build_envp() const {
    char **envp = new char*[_taskData.env().size() + 1];
    std::size_t i(0);
    for (TaskData::env_t::const_iterator it = _taskData.env().begin(); it != _taskData.env().end(); it++) {
        const std::string k(it->first);
        const std::string v(it->second);
        // len(k) + len("=") + len(v) + zero-termination
        const std::string::size_type len(k.size() + 1 + v.size() + 1);

        envp[i] = new char[len+1];
        snprintf(envp[i], len, "%s=%s", k.c_str(), v.c_str());
        envp[i][len] = (char)0;
        ++i;
    }
    envp[_taskData.env().size()] = (char*)0;
    return envp;
}


#include "Task.hpp"

#include <unistd.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/wait.h>
#include <signal.h>

using namespace xbe;

Task::Task(const boost::filesystem::path &path)
    : XBE_INIT_LOGGER("xbe.task:"+path.string()), _path(path), _workingDir(),
    _uid(getuid()), _gid(getgid()),
    _pid(0), _status(UNKNOWN), _exitCode(0), _taskListener(0), _barrier(2)

{
    char buf[PATH_MAX];
    getcwd(buf, sizeof(buf));
    _workingDir = buf;
    _params.push_back(path.string());
}

Task::~Task() {}

void Task::operator()() {
    // wait until the sub process has been started
    // observe the created sub processes from within a thread.
    _barrier.wait();
    if (pid() > 0) {
        waitpid(pid(), &_exitCode, 0);
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
            _taskListener->onTaskExit(*this);
        }
    } else if (pid() < 0) {
        {
            boost::unique_lock<boost::recursive_mutex> lock(_mtx);
            _status = FAILED;
            _exitCode = errno;
        }

        if (_taskListener) {
            _taskListener->onTaskFailure(*this);
        }
    }
    _thread.detach();
    _cond.notify_one();
}

void Task::wait() {
    boost::unique_lock<boost::recursive_mutex> lock(_mtx);
    if (running()) {
        while (status() == UNKNOWN )
            _cond.wait(lock);
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

        _pid = fork();
        if (_pid == 0) {
            // close open file descriptors
            for (int fd = 0; fd < 1024; fd++)
                close(fd);
            // redirect stdin stdout stderr
            if (!_pathStdin.empty()) {
                int fd = open(_pathStdin.string().c_str(), O_RDONLY);
                dup2(fd, 0);
            }
            if (!_pathStdout.empty()) {
                int fd = open(_pathStdout.string().c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0600);
                dup2(fd, 1);
            }
            if (!_pathStderr.empty()) {
                int fd = open(_pathStderr.string().c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0600);
                dup2(fd, 2);
            }

            // set uid, gid
            setuid(uid());
            setgid(gid());

            // set working directory
            chdir(wd().string().c_str());

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
    char **argv = new char*[_params.size() + 1];

    for (std::size_t i = 0; i < _params.size(); i++) {
        const std::string::size_type len(_params[i].size());

        argv[i] = new char[len+1];
        strncpy(argv[i], _params[i].c_str(), len);
        argv[i][len] = (char)0;
    }
    argv[_params.size()] = (char*)0;
    return argv;
}

char **Task::build_envp() const {
    char **envp = new char*[_env.size() + 1];
    std::size_t i(0);
    for (env_t::const_iterator it = _env.begin(); it != _env.end(); it++) {
        const std::string k(it->first);
        const std::string v(it->second);
        // len(k) + len("=") + len(v) + zero-termination
        const std::string::size_type len(k.size() + 1 + v.size() + 1);

        envp[i] = new char[len+1];
        snprintf(envp[i], len, "%s=%s", k.c_str(), v.c_str());
        envp[i][len] = (char)0;
        ++i;
    }
    envp[_env.size()] = (char*)0;
    return envp;
}


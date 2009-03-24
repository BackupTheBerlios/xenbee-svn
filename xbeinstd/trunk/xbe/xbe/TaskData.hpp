#ifndef XBE_TASK_DATA_HPP
#define XBE_TASK_DATA_HPP 1

#include <string>
#include <list>
#include <map>

#include <sys/types.h>
#include <unistd.h>

#include <boost/filesystem.hpp>

namespace xbe {
    class TaskData {
        public:
            typedef std::map<std::string, std::string> env_t;
            typedef std::vector<std::string> params_t;

            explicit
            TaskData(const boost::filesystem::path &path = "");

            virtual ~TaskData() {}

            bool is_valid() const { return (! path().empty()); }

            const env_t & env() const { return _env; }
            env_t & env() { return _env; }

            const params_t & params() const { return _params; }
            params_t & params() { return _params; }

            const std::string & path() const { return _params.front(); }
            std::string & path() { return _params.front(); }

            const boost::filesystem::path & wd() const { return _workingDir; }
            boost::filesystem::path & wd() { return _workingDir; }
            void wd(const boost::filesystem::path & p) { _workingDir = p; }

            bool executable() const;

            const uid_t & uid() const { return _uid; }
            uid_t & uid() { return _uid; }

            const gid_t & gid() const { return _gid; }
            gid_t & gid() { return _gid; }

            const std::string stdIn()  const { return _pathStdin.string(); }
            const std::string stdOut() const { return _pathStdout.string(); }
            const std::string stdErr() const { return _pathStderr.string(); }

            void stdIn (const boost::filesystem::path &path) { _pathStdin  = path; }
            void stdOut(const boost::filesystem::path &path) { _pathStdout = path; }
            void stdErr(const boost::filesystem::path &path) { _pathStderr = path; }
        private:
            boost::filesystem::path _workingDir;

            boost::filesystem::path _pathStdin;
            boost::filesystem::path _pathStdout;
            boost::filesystem::path _pathStderr;

            params_t _params;
            env_t _env;
            uid_t _uid;
            gid_t _gid;
    };
}

#endif // ! XBE_TASK_DATA_HPP

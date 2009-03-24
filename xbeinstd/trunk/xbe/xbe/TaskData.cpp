#include "TaskData.hpp"

#include <unistd.h>
#include <errno.h>
#include <sys/types.h>

using namespace xbe;

TaskData::TaskData(const boost::filesystem::path &path)
    : _workingDir(), _params(1, path.string()), _uid(getuid()), _gid(getgid())
{
    char buf[PATH_MAX];
    getcwd(buf, sizeof(buf));
    _workingDir = buf;
}

bool TaskData::executable() const {
    // check if path exists and whether it is executable
    if (access(path().c_str(), X_OK) == 0) {
        return true;
    } else {
        return false;
    }
}

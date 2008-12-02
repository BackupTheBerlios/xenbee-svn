#include "TaskData.hpp"

#include <unistd.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/stat.h>

using namespace xbe;

TaskData::TaskData(const boost::filesystem::path &path)
    : _workingDir(), _params(1, path.string()), _uid(getuid()), _gid(getgid())
{
    char buf[PATH_MAX];
    getcwd(buf, sizeof(buf));
    _workingDir = buf;
}

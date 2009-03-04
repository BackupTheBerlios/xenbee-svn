#include "lib_compat.hpp"

#ifdef MQS_WINDOWS
#include <windows.h>

int
getpid(void)
{
    return GetCurrentThreadId();
}

#endif

#include "util.hpp"
#include <time.h>
#include <sys/time.h>

namespace seda {
    unsigned long long getCurrentTimeMilliseconds() {
        struct timeval now;
        gettimeofday(&now, NULL);
        return now.tv_sec * 1000 + now.tv_usec;
    }
}

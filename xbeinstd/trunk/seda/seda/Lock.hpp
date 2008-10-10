#ifndef SEDA_LOCK_HPP
#define SEDA_LOCK_HPP 1

#include <seda/Synchronizable.hpp>

namespace seda {
    /**
     * Implements a resource manager for synchronizable objects
     */
    class Lock {
        public:
            explicit
            Lock(seda::Synchronizable &resource) : _resource(resource) {
                _resource.acquire();
            }
            ~Lock() {
                _resource.release();
            }
        private:
            seda::Synchronizable &_resource;
    };
}

#endif

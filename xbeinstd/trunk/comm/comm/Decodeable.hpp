#ifndef SEDA_COMM_DECODEABLE_HPP
#define SEDA_COMM_DECODEABLE_HPP 1

#include <string>

namespace seda {
namespace comm {
    class Decodeable {
    public:
        virtual void decode() = 0;
    };
}}

#endif

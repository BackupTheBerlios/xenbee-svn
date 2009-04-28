#ifndef SEDA_COMM_ENCODEABLE_HPP
#define SEDA_COMM_ENCODEABLE_HPP 1

#include <string>

namespace seda {
namespace comm {
    class Encodeable {
    public:
        virtual std::string encode() const = 0;
    };
}}

#endif

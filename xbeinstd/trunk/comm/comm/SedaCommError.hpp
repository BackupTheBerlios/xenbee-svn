#ifndef SEDA_COMM_ERROR_HPP
#define SEDA_COMM_ERROR_HPP 1

#include <stdexcept>

namespace seda {
namespace comm {
    class SedaCommError : public std::runtime_error {
    public:
        SedaCommError(const std::string &errorMessage)
            : std::runtime_error(errorMessage) {}

        virtual ~SedaCommError() throw () {}
    };
}}

#endif

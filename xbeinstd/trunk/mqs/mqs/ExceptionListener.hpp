#ifndef MQS_EXCEPTION_LISTENER_HPP
#define MQS_EXCEPTION_LISTENER_HPP 1

#include <cms/CMSException.h>
#include <mqs/MQSException.hpp>

namespace mqs {
    class ExceptionListener {
    public:
        virtual void onException(const cms::CMSException &) = 0;
        virtual void onException(const mqs::MQSException &) = 0;
    };
}

#endif // ! MQS_MESSAGE_LISTENER_HPP

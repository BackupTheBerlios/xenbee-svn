#ifndef MQS_MQSEXCEPTION_HPP
#define MQS_MQSEXCEPTION_HPP 1

#include <string>
#include <exception>

namespace mqs 
{
    class MQSException : public std::exception {
    public:
        explicit
        MQSException(const std::string& reason)
            : _reason(reason) {}
        virtual ~MQSException() throw() {}

        virtual const char* what() const throw() { return reason().c_str(); }
        virtual const std::string& reason() const { return _reason; }

    private:
        std::string _reason;
    };    
}

#endif // ! MQS_MQSEXCEPTION

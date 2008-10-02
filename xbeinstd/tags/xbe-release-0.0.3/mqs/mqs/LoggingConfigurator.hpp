#ifndef MQS_LOGGINGCONFIGURATOR_HPP
#define MQS_LOGGINGCONFIGURATOR_HPP 1

#include <iostream>

#if HAVE_LOG4CPP
#include <log4cpp/Category.hh>
#include <log4cpp/BasicConfigurator.hh>
#include <log4cpp/Priority.hh>
#endif

namespace mqscommon 
{
    class ConfigurationFunction {
    public:
        virtual void operator() () throw() = 0;
    };

    class DefaultConfiguration : public ConfigurationFunction {
    public:
        virtual void operator() () throw() {
#if HAVE_LOG4CPP
            try {
                ::log4cpp::BasicConfigurator::configure();
                ::log4cpp::Category::setRootPriority(::log4cpp::Priority::DEBUG);
            } catch (const std::exception& ex) {
                std::clog << "Could not configure the logging environment: " << ex.what() << std::endl;
            } catch (...) {
                std::clog << "Could not configure the logging environment: " << "unknown error" << std::endl;
            }
#endif
        }
    };

    class LoggingConfigurator {
    public:
        static void configure() {
            DefaultConfiguration()();
        }
        static void configure(ConfigurationFunction* c) {
            (*c)();
        }
    };
}

#endif // ! MQS_LOGGINGCONFIGURATOR_HPP

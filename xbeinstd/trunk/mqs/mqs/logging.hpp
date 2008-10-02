#ifndef MQS_LOGGING_HPP
#define MQS_LOGGING_HPP 1

/* Logging */
#if ENABLE_LOGGING

#include <mqs/LoggingConfigurator.hpp>

#if HAVE_LOG4CXX
#include <log4cxx/logger.h>

#define MQS_LDECLARE_LOGGER(logger)           ::log4cxx::LoggerPtr logger
#define MQS_LDEFINE_LOGGER(logger, hierarchy) ::log4cxx::LoggerPtr MQS_LINIT_LOGGER(logger, hierarchy)
#define MQS_LINIT_LOGGER(logger, hierarchy)   logger(::log4cxx::Logger::getLogger(hierarchy))

#define MQS_DECLARE_LOGGER()         MQS_LDECLARE_LOGGER(mqs_logger)
#define MQS_DEFINE_LOGGER(hierarchy) MQS_LDEFINE_LOGGER(mqs_logger, hierarchy)
#define MQS_INIT_LOGGER(hierarchy)   MQS_LINIT_LOGGER(mqs_logger, hierarchy)

#define MQS_LLOG_DEBUG(logger, msg) LOG4CXX_DEBUG(logger, msg)
#define MQS_LLOG_INFO(logger, msg)  LOG4CXX_INFO(logger, msg)
#define MQS_LLOG_WARN(logger, msg)  LOG4CXX_WARN(logger, msg)
#define MQS_LLOG_ERROR(logger, msg) LOG4CXX_ERROR(logger, msg)
#define MQS_LLOG_FATAL(logger, msg) LOG4CXX_FATAL(logger, msg)

#define MQS_LOG_DEBUG(msg) MQS_LLOG_DEBUG(mqs_logger, msg)
#define MQS_LOG_INFO(msg)  MQS_LLOG_INFO(mqs_logger, msg) 
#define MQS_LOG_WARN(msg)  MQS_LLOG_WARN(mqs_logger, msg) 
#define MQS_LOG_ERROR(msg) MQS_LLOG_ERROR(mqs_logger, msg)
#define MQS_LOG_FATAL(msg) MQS_LLOG_FATAL(mqs_logger, msg)

#elif HAVE_LOG4CPP /* ! HAVE_LOG4CXX */

#include <log4cpp/Category.hh>
#include <log4cpp/convenience.h>

#define MQS_LDECLARE_LOGGER(logger)           ::log4cpp::Category& logger
#define MQS_LDEFINE_LOGGER(logger, hierarchy) ::log4cpp::Category& MQS_LINIT_LOGGER(logger, hierarchy)
#define MQS_LINIT_LOGGER(logger, hierarchy)   logger(::log4cpp::Category::getInstance(hierarchy))

#define MQS_DECLARE_LOGGER()         MQS_LDECLARE_LOGGER(mqs_logger)
#define MQS_DEFINE_LOGGER(hierarchy) MQS_LDEFINE_LOGGER(mqs_logger, hierarchy)
#define MQS_INIT_LOGGER(hierarchy)   MQS_LINIT_LOGGER(mqs_logger, hierarchy)

#define MQS_LLOG_DEBUG(logger, msg) LOG4CPP_DEBUG_S(logger) << msg
#define MQS_LLOG_INFO(logger, msg)  LOG4CPP_INFO_S(logger)  << msg
#define MQS_LLOG_WARN(logger, msg)  LOG4CPP_WARN_S(logger)  << msg
#define MQS_LLOG_ERROR(logger, msg) LOG4CPP_ERROR_S(logger) << msg
#define MQS_LLOG_FATAL(logger, msg) LOG4CPP_FATAL_S(logger) << msg

#define MQS_LOG_DEBUG(msg) MQS_LLOG_DEBUG(mqs_logger, msg)
#define MQS_LOG_INFO(msg)  MQS_LLOG_INFO(mqs_logger, msg) 
#define MQS_LOG_WARN(msg)  MQS_LLOG_WARN(mqs_logger, msg) 
#define MQS_LOG_ERROR(msg) MQS_LLOG_ERROR(mqs_logger, msg)
#define MQS_LOG_FATAL(msg) MQS_LLOG_FATAL(mqs_logger, msg)

#else
#error Logging has been enabled, but no usable logging mechanism available!
#endif

#else /* ! ENABLE_LOGGING */

#define MQS_LDECLARE_LOGGER(logger)   void* __mqs_unused_##logger
#define MQS_LDEFINE_LOGGER(logger, h)
#define MQS_LINIT_LOGGER(logger, h)   __mqs_unused_##logger(0)

#define MQS_DECLARE_LOGGER()          MQS_LDECLARE_LOGGER(logger)
#define MQS_DEFINE_LOGGER(hierarchy)  MQS_LDEFINE_LOGGER(logger, hierarchy)
#define MQS_INIT_LOGGER(hierarchy)    MQS_LINIT_LOGGER(logger, hierarchy)

#define MQS_LLOG_DEBUG(logger, msg) 
#define MQS_LLOG_INFO(logger, msg)  
#define MQS_LLOG_WARN(logger, msg)  
#define MQS_LLOG_ERROR(logger, msg) 
#define MQS_LLOG_FATAL(logger, msg) 

#define MQS_LOG_DEBUG(msg) 
#define MQS_LOG_INFO(msg)  
#define MQS_LOG_WARN(msg)  
#define MQS_LOG_ERROR(msg) 
#define MQS_LOG_FATAL(msg) 

#endif

#endif // !MQS_LOGGING_HPP

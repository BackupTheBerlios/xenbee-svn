#ifndef SEDA_LOGGING_HPP
#define SEDA_LOGGING_HPP 1

/* Logging */
#if HAVE_LOG4CXX
#include <log4cxx/logger.h>

#define LDECLARE_LOGGER(logger)           ::log4cxx::LoggerPtr logger
#define LDEFINE_LOGGER(logger, hierarchy) ::log4cxx::LoggerPtr LINIT_LOGGER(logger, hierarchy)
#define LINIT_LOGGER(logger, hierarchy)   logger(::log4cxx::Logger::getLogger(hierarchy))

#define DECLARE_LOGGER()         LDECLARE_LOGGER(logger)
#define DEFINE_LOGGER(hierarchy) LDEFINE_LOGGER(logger, hierarchy)
#define INIT_LOGGER(hierarchy)   LINIT_LOGGER(logger, hierarchy)

#define LLOG_DEBUG(logger, msg) LOG4CXX_DEBUG(logger, msg)
#define LLOG_INFO(logger, msg)  LOG4CXX_INFO(logger, msg)
#define LLOG_WARN(logger, msg)  LOG4CXX_WARN(logger, msg)
#define LLOG_ERROR(logger, msg) LOG4CXX_ERROR(logger, msg)
#define LLOG_FATAL(logger, msg) LOG4CXX_FATAL(logger, msg)

#define LOG_DEBUG(msg) LLOG_DEBUG(logger, msg)
#define LOG_INFO(msg)  LLOG_INFO(logger, msg) 
#define LOG_WARN(msg)  LLOG_WARN(logger, msg) 
#define LOG_ERROR(msg) LLOG_ERROR(logger, msg)
#define LOG_FATAL(msg) LLOG_FATAL(logger, msg)

#else /* ! HAVE_LOG4CXX */

#define LDECLARE_LOGGER(logger)   void* __unused_##logger
#define LDEFINE_LOGGER(logger, h)
#define LINIT_LOGGER(logger, h)   __unused_##logger(0)

#define DECLARE_LOGGER()          LDECLARE_LOGGER(logger)
#define DEFINE_LOGGER(hierarchy)  LDEFINE_LOGGER(logger, hierarchy)
#define INIT_LOGGER(hierarchy)    LINIT_LOGGER(logger, hierarchy)

#define LOG_DEBUG(msg) 
#define LOG_INFO(msg)  
#define LOG_WARN(msg)  
#define LOG_ERROR(msg) 
#define LOG_FATAL(msg) 

#endif


#endif // !SEDA_LOGGING_HPP

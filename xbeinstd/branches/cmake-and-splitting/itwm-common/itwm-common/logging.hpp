#ifndef ITWM_HPC_LOGGING_HPP
#define ITWM_HPC_LOGGING_HPP 1

/* Logging */
#if ENABLE_LOGGING

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

#elif HAVE_LOG4CPP /* ! HAVE_LOG4CXX */

#include <log4cpp/Category.hh>
#include <log4cpp/convenience.h>
#include <iostream>

#define LDECLARE_LOGGER(logger)           ::log4cpp::Category& logger
#define LDEFINE_LOGGER(logger, hierarchy) ::log4cpp::Category& LINIT_LOGGER(logger, hierarchy)
#define LINIT_LOGGER(logger, hierarchy)   logger(::log4cpp::Category::getInstance(hierarchy))

#define DECLARE_LOGGER()         LDECLARE_LOGGER(logger)
#define DEFINE_LOGGER(hierarchy) LDEFINE_LOGGER(logger, hierarchy)
#define INIT_LOGGER(hierarchy)   LINIT_LOGGER(logger, hierarchy)

#define LLOG_DEBUG(logger, msg) LOG4CPP_DEBUG_S(logger) << msg
#define LLOG_INFO(logger, msg)  LOG4CPP_INFO_S(logger)  << msg
#define LLOG_WARN(logger, msg)  LOG4CPP_WARN_S(logger)  << msg
#define LLOG_ERROR(logger, msg) LOG4CPP_ERROR_S(logger) << msg
#define LLOG_FATAL(logger, msg) LOG4CPP_FATAL_S(logger) << msg

#define LOG_DEBUG(msg) LLOG_DEBUG(logger, msg)
#define LOG_INFO(msg)  LLOG_INFO(logger, msg) 
#define LOG_WARN(msg)  LLOG_WARN(logger, msg) 
#define LOG_ERROR(msg) LLOG_ERROR(logger, msg)
#define LOG_FATAL(msg) LLOG_FATAL(logger, msg)

#else
#error Logging has been enabled, but no usable logging mechanism available!
#endif

#else /* ! ENABLE_LOGGING */

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

#endif // !ITWM_HPC_LOGGING_HPP

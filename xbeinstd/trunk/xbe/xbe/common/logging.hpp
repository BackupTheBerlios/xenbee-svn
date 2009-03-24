#ifndef XBE_COMMON_LOGGING_HPP
#define XBE_COMMON_LOGGING_HPP 1

/* Logging */
#if ENABLE_LOGGING == 1

#if HAVE_LOG4CXX
#include <log4cxx/logger.h>

#define XBE_LDECLARE_LOGGER(logger)           ::log4cxx::LoggerPtr logger
#define XBE_LDEFINE_LOGGER(logger, hierarchy) ::log4cxx::LoggerPtr XBE_LINIT_LOGGER(logger, hierarchy)
#define XBE_LINIT_LOGGER(logger, hierarchy)   logger(::log4cxx::Logger::getLogger(hierarchy))

#define XBE_DECLARE_LOGGER()         XBE_LDECLARE_LOGGER(xbe_logger)
#define XBE_DEFINE_LOGGER(hierarchy) XBE_LDEFINE_LOGGER(xbe_logger, hierarchy)
#define XBE_INIT_LOGGER(hierarchy)   XBE_LINIT_LOGGER(xbe_logger, hierarchy)

#define XBE_LLOG_DEBUG(logger, msg) LOG4CXX_DEBUG(logger, msg)
#define XBE_LLOG_INFO(logger, msg)  LOG4CXX_INFO(logger, msg)
#define XBE_LLOG_WARN(logger, msg)  LOG4CXX_WARN(logger, msg)
#define XBE_LLOG_ERROR(logger, msg) LOG4CXX_ERROR(logger, msg)
#define XBE_LLOG_FATAL(logger, msg) LOG4CXX_FATAL(logger, msg)

#define XBE_LOG_DEBUG(msg) XBE_LLOG_DEBUG(xbe_logger, msg)
#define XBE_LOG_INFO(msg)  XBE_LLOG_INFO(xbe_logger, msg) 
#define XBE_LOG_WARN(msg)  XBE_LLOG_WARN(xbe_logger, msg) 
#define XBE_LOG_ERROR(msg) XBE_LLOG_ERROR(xbe_logger, msg)
#define XBE_LOG_FATAL(msg) XBE_LLOG_FATAL(xbe_logger, msg)

#elif HAVE_LOG4CPP /* ! HAVE_LOG4CXX */

#include <log4cpp/Category.hh>
#include <log4cpp/convenience.h>

#define XBE_LDECLARE_LOGGER(logger)           ::log4cpp::Category& logger
#define XBE_LDEFINE_LOGGER(logger, hierarchy) ::log4cpp::Category& XBE_LINIT_LOGGER(logger, hierarchy)
#define XBE_LINIT_LOGGER(logger, hierarchy)   logger(::log4cpp::Category::getInstance(hierarchy))

#define XBE_DECLARE_LOGGER()         XBE_LDECLARE_LOGGER(xbe_logger)
#define XBE_DEFINE_LOGGER(hierarchy) XBE_LDEFINE_LOGGER(xbe_logger, hierarchy)
#define XBE_INIT_LOGGER(hierarchy)   XBE_LINIT_LOGGER(xbe_logger, hierarchy)

#define XBE_LLOG_DEBUG(logger, msg) LOG4CPP_DEBUG_S(logger) << msg
#define XBE_LLOG_INFO(logger, msg)  LOG4CPP_INFO_S(logger)  << msg
#define XBE_LLOG_WARN(logger, msg)  LOG4CPP_WARN_S(logger)  << msg
#define XBE_LLOG_ERROR(logger, msg) LOG4CPP_ERROR_S(logger) << msg
#define XBE_LLOG_FATAL(logger, msg) LOG4CPP_FATAL_S(logger) << msg

#define XBE_LOG_DEBUG(msg) XBE_LLOG_DEBUG(xbe_logger, msg)
#define XBE_LOG_INFO(msg)  XBE_LLOG_INFO(xbe_logger, msg) 
#define XBE_LOG_WARN(msg)  XBE_LLOG_WARN(xbe_logger, msg) 
#define XBE_LOG_ERROR(msg) XBE_LLOG_ERROR(xbe_logger, msg)
#define XBE_LOG_FATAL(msg) XBE_LLOG_FATAL(xbe_logger, msg)

#else

#warn Logging has been enabled, but no usable logging mechanism available, disabling it!
#undef ENABLE_LOGGING
#define ENABLE_LOGGING 0

#endif // HAVE_LOG4CPP
#endif // ENABLE_LOGGING == 1

#if ENABLE_LOGGING == 0 /* ! ENABLE_LOGGING */

#define XBE_LDECLARE_LOGGER(logger)   void* __xbe_unused_##logger
#define XBE_LDEFINE_LOGGER(logger, h)
#define XBE_LINIT_LOGGER(logger, h)   __xbe_unused_##logger(0)

#define XBE_DECLARE_LOGGER()          XBE_LDECLARE_LOGGER(logger)
#define XBE_DEFINE_LOGGER(hierarchy)  XBE_LDEFINE_LOGGER(logger, hierarchy)
#define XBE_INIT_LOGGER(hierarchy)    XBE_LINIT_LOGGER(logger, hierarchy)

#define XBE_LLOG_DEBUG(logger, msg) 
#define XBE_LLOG_INFO(logger, msg)  
#define XBE_LLOG_WARN(logger, msg)  
#define XBE_LLOG_ERROR(logger, msg) 
#define XBE_LLOG_FATAL(logger, msg) 

#define XBE_LOG_DEBUG(msg) 
#define XBE_LOG_INFO(msg)  
#define XBE_LOG_WARN(msg)  
#define XBE_LOG_ERROR(msg) 
#define XBE_LOG_FATAL(msg) 

#endif

#endif // !XBE_LOGGING_HPP

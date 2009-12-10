/* 
   Copyright (C) 2009 Alexander Petry <alexander.petry@itwm.fraunhofer.de>.

   This file is part of seda.

   seda is free software; you can redistribute it and/or modify it
   under the terms of the GNU General Public License as published by the
   Free Software Foundation; either version 2, or (at your option) any
   later version.

   seda is distributed in the hope that it will be useful, but WITHOUT
   ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
   FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
   for more details.

   You should have received a copy of the GNU General Public License
   along with seda; see the file COPYING.  If not, write to
   the Free Software Foundation, Inc., 59 Temple Place - Suite 330,
   Boston, MA 02111-1307, USA.  

*/

#ifndef MQS_LOGGING_HPP
#define MQS_LOGGING_HPP 1

/* Logging */
#if ENABLE_LOGGING == 1

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

#define MQS_LLOG_DEBUG(logger, msg) LOG4CPP_DEBUG_S(logger) << __PRETTY_FUNCTION__ << ":" << __LINE__ << ": " << msg
#define MQS_LLOG_INFO(logger, msg)  LOG4CPP_INFO_S(logger)  << __PRETTY_FUNCTION__ << ":" << __LINE__ << ": " << msg
#define MQS_LLOG_WARN(logger, msg)  LOG4CPP_WARN_S(logger)  << __PRETTY_FUNCTION__ << ":" << __LINE__ << ": " << msg
#define MQS_LLOG_ERROR(logger, msg) LOG4CPP_ERROR_S(logger) << __PRETTY_FUNCTION__ << ":" << __LINE__ << ": " << msg
#define MQS_LLOG_FATAL(logger, msg) LOG4CPP_FATAL_S(logger) << __PRETTY_FUNCTION__ << ":" << __LINE__ << ": " << msg

#define MQS_LOG_DEBUG(msg) MQS_LLOG_DEBUG(mqs_logger, msg)
#define MQS_LOG_INFO(msg)  MQS_LLOG_INFO(mqs_logger, msg) 
#define MQS_LOG_WARN(msg)  MQS_LLOG_WARN(mqs_logger, msg) 
#define MQS_LOG_ERROR(msg) MQS_LLOG_ERROR(mqs_logger, msg)
#define MQS_LOG_FATAL(msg) MQS_LLOG_FATAL(mqs_logger, msg)

#else
#warn Logging has been enabled, but no usable logging mechanism available!
#undef ENABLE_LOGGING
#define ENABLE_LOGGING 0
#endif

#endif

#if ENABLE_LOGGING == 0 /* ! ENABLE_LOGGING */

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

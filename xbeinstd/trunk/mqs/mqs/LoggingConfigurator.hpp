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

#ifndef MQS_LOGGINGCONFIGURATOR_HPP
#define MQS_LOGGINGCONFIGURATOR_HPP 1

#include <iostream>

#if HAVE_LOG4CPP
#include <log4cpp/Category.hh>
#include <log4cpp/BasicConfigurator.hh>
#include <log4cpp/Priority.hh>
#include <log4cpp/PatternLayout.hh>
#endif

namespace mqscommon 
{
    class ConfigurationFunction {
    public:
      virtual ~ConfigurationFunction() {}
        virtual void operator() () throw() = 0;
    };

    class DefaultConfiguration : public ConfigurationFunction {
    public:
      virtual ~DefaultConfiguration() {}
        virtual void operator() () throw() {
#if HAVE_LOG4CPP
            try {
                ::log4cpp::BasicConfigurator::configure();
                const ::log4cpp::AppenderSet appenders(::log4cpp::Category::getRoot().getAllAppenders());
                for (::log4cpp::AppenderSet::const_iterator it(appenders.begin()); it != appenders.end(); it++) {
                    std::clog << "found appender: " << (*it)->getName() << std::endl;
                    ::log4cpp::PatternLayout *pl(new ::log4cpp::PatternLayout());
//                    pl->setConversionPattern(::log4cpp::PatternLayout::TTCC_CONVERSION_PATTERN);
                    pl->setConversionPattern("%R %p %c %x - %m%n");
                    (*it)->setLayout(pl);
                }
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
      virtual ~LoggingConfigurator() {}
        static void configure() {
            DefaultConfiguration()();
        }
        static void configure(ConfigurationFunction* c) {
            (*c)();
        }
    };
}

#endif // ! MQS_LOGGINGCONFIGURATOR_HPP

## Makefile.am -- Process this file with automake to produce Makefile.in

AM_CPPFLAGS = -I$(top_builddir) -I$(top_srcdir) $(ACTIVEMQ_CFLAGS)
if BUILD_WITH_LOGGING
  AM_CPPFLAGS += $(LOG4CXX_CFLAGS)
endif

if BUILD_WITH_LOGGING
  LIBADD = $(LOG4CXX_LIBS)
endif

lib_LTLIBRARIES      = libseda.la
libseda_la_LIBADD     = $(top_builddir)/replace/libreplace.la $(ACTIVEMQ_LIBS)
libseda_la_SOURCES    = constants.hpp constants.cpp\
                        SedaException.hpp IEvent.hpp StringEvent.hpp\
                        IEventQueue.hpp EventQueue.hpp\
                        StageWorker.hpp StageWorker.cpp\
                        Stage.hpp Stage.cpp Strategy.hpp\
                        StrategyDecorator.hpp StrategyDecorator.cpp\
                        CompositeStrategy.hpp CompositeStrategy.cpp\
                        LoggingStrategy.hpp DiscardStrategy.hpp\
                        ForwardStrategy.hpp ForwardStrategy.cpp\
                        CoutStrategy.hpp CoutStrategy.cpp

#libseda_configdir     = $(libdir)/libseda-@VERSION@/include
#libseda_config_DATA   = $(top_srcdir)/config.h

libseda_includedir      = $(includedir)/seda-@VERSION@/seda
libseda_include_HEADERS = constants.hpp IEvent.hpp IEventQueue.hpp EventQueue.hpp\
                          StageWorker.hpp SedaException.hpp Stage.hpp\
                          EventDecorator.hpp Strategy.hpp StrategyDecorator.hpp\
                          LoggingStrategy.hpp ForwardStrategy.hpp CoutStrategy.hpp\
                          DiscardStrategy.hpp EventCountStrategy.hpp StringEvent.hpp\
                          CompositeStrategy.hpp

# extra objects to link to the library as determined by configure
#libhelloat_la_LDADD    = <dummyobject.o> @LTLIBOBJ@ 

# to specify special linker options use
#libhelloat_la_LDFLAGS = -version-info 1:2:3

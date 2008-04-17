## Makefile.am -- Process this file with automake to produce Makefile.in

AM_CPPFLAGS             =  -I$(top_builddir) -I$(top_srcdir) $(ACTIVEMQ_CFLAGS) $(LOG4CXX_CFLAGS)

lib_LTLIBRARIES      = libmqs.la
libmqs_la_LIBADD     = $(top_builddir)/replace/libreplace.la $(ACTIVEMQ_LIBS) $(LOG4CXX_LIBS)

libmqs_la_SOURCES    = common.h common.cpp logging.hpp error.h error.cpp \
                       Response.hpp DestinationProperties.hpp DestinationProperties.cpp\
                       Destination.hpp Destination.cpp\
                       Channel.hpp Channel.cpp BrokerURI.hpp
#libmqs_configdir     = $(libdir)/libmqs-@VERSION@/include
#libmqs_config_DATA   = $(top_srcdir)/config.h

libmqs_includedir    = $(includedir)/mqs-@VERSION@/mqs
libmqs_include_HEADERS = common.h error.h logging.hpp Response.hpp Destination.hpp\
                         DestinationProperties.hpp Channel.hpp BrokerURI.hpp

# extra objects to link to the library as determined by configure
#libhelloat_la_LDADD    = <dummyobject.o> @LTLIBOBJ@ 

# to specify special linker options use
#libhelloat_la_LDFLAGS = -version-info 1:2:3

## Makefile.am -- Process this file with automake to produce Makefile.in

EXTRA_DIST = log4j.xml

AM_CPPFLAGS             =  -I$(top_builddir) -I$(top_srcdir)\
                           $(ACTIVEMQ_CFLAGS) $(CPPUNIT_CFLAGS) $(LOG4CXX_CFLAGS)

TESTS			= test

check_PROGRAMS          = test
test_SOURCES            = main.cpp testsconfig.hpp\
                          DestinationTest.hpp DestinationTest.cpp\
                          ChannelTest.hpp ChannelTest.cpp
test_LDADD              = $(top_builddir)/mqs/libmqs.la $(CPPUNIT_LIBS) $(LOG4CXX_LIBS)

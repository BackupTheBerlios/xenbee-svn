## Makefile.am -- Process this file with automake to produce Makefile.in

EXTRA_DIST = log4j.xml

AM_CPPFLAGS = -I$(top_builddir) -I$(top_srcdir) -I$(top_srcdir)/seda -I$(top_srcdir)/xbe\
              $(ACTIVEMQ_CFLAGS) $(CPPUNIT_CFLAGS)\
              $(XERCES_CFLAGS) $(XML_SECURITY_CFLAGS)

TESTS			= test

check_PROGRAMS          = test
test_SOURCES            = main.cpp testsconfig.hpp\
                          ChannelEventQueueAdapterTest.hpp ChannelEventQueueAdapterTest.cpp\
                          XMLEncodeDecodeTest.hpp XMLEncodeDecodeTest.cpp\
                          XMLSecurityTest.hpp XMLSecurityTest.cpp\
                          XMLSecurityLibraryTest.hpp XMLSecurityLibraryTest.cpp
test_LDADD              = $(top_builddir)/mqs/mqs/libmqs.la\
                          $(top_builddir)/seda/seda/libseda.la\
                          $(top_builddir)/xbe/libxbe.la\
                          $(CPPUNIT_LIBS)\
                          $(ACTIVEMQ_LIBS)\
                          $(XERCES_LDFLAGS)\
                          $(XML_SECURITY_LDFLAGS)\
                          $(LOG4CXX_LIBS)


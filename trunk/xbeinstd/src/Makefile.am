## Makefile.am -- Process this file with automake to produce Makefile.in

AM_CPPFLAGS             =  -I$(top_builddir) -I$(top_srcdir) -I$(top_srcdir)/mqs $(ACTIVEMQ_CFLAGS)

bin_PROGRAMS            = mqstest
mqstest_SOURCES         = test.cpp
mqstest_LDADD           = $(top_builddir)/mqs/mqs/libmqs.la

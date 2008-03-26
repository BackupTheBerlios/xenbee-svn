## Makefile.am -- Process this file with automake to produce Makefile.in

AM_CPPFLAGS             =  -I$(top_builddir) -I$(top_srcdir) $(ACTIVEMQ_CFLAGS)

bin_PROGRAMS            = mqstest
mqstest_SOURCES         = test.cpp
mqstest_LDADD           = $(top_builddir)/mqs/libmqs.la


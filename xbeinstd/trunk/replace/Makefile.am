## Makefile.am -- Process this file with automake to produce Makefile.in

# This directory contains implementations for replacement functions that are
# conditionally linked into the final library only when needed.
#
# If no replacement is needed, the resulting libreplace will be empty
#
#MAINTAINERCLEANFILES    = Makefile.in

AM_CPPFLAGS              =  -I$(top_builddir) -I$(top_srcdir)

noinst_LTLIBRARIES       = libreplace.la
libreplace_la_SOURCES    = 
libreplace_la_LIBADD     = @LTLIBOBJS@

# the LIBOBJS/LTLIBOBJS will only contain entries, if a replacement is needed
# uncomment the following line, if there is a AC_REPLACE_FUNCS in configure.in.
# It depends on whether you use RANLIB or LIBTOOL to generate the libraries,
# here we use libtool, so LTLIBOBJS is required.
#


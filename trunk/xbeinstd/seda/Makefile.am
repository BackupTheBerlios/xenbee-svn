## Makefile.am -- Process this file with automake to produce Makefile.in

# this is the toplevel makefile of our project, build replacement functions
# before building the rest

#MAKEFLAGS=-s # be silent by default
ACLOCAL_AMFLAGS = -I m4 --install
DISTCHECK_CONFIGURE_FLAGS += --enable-debug
EXTRA_DIST = bootstrap m4/ log4j.properties log4j.xml

# add doxygen support
#include $(top_srcdir)/m4/doxygen.am

if BUILD_UNIT_TESTS
    MAYBE_TESTS = tests
endif

SUBDIRS = replace seda $(MAYBE_TESTS)

pkgconfigdir = $(libdir)/pkgconfig
pkgconfig_DATA = libseda.pc

# build debian packages
deb:
	dpkg-buildpackage -rfakeroot

rpm: xbeinstd.spec
	rpmbuild $<

clean-local: clean-emacs-backups

clean-emacs-backups:
	-find . -name "*~" -delete


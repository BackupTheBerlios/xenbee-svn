## Makefile.am -- Process this file with automake to produce Makefile.in

EXTRA_DIST = Task.sm Task_sm.h Task_sm.cpp statemap.h

AM_CPPFLAGS = -I$(top_builddir) -I$(top_srcdir) -I$(top_srcdir)/seda -I$(top_srcdir)/mqs \
              $(ACTIVEMQ_CFLAGS) $(XERCES_CFLAGS)\
              $(XML_SECURITY_CFLAGS) $(SMC_CFLAGS)\
              $(LOG4CXX_CFLAGS)

lib_LTLIBRARIES      = libxbe.la
#libxbe_la_LIBADD     = $(top_builddir)/replace/libreplace.la $(top_builddir)/mqs/libmqs.la\
#                       $(XERCES_LDFLAGS) $(XML_SECURITY_LDFLAGS) $(ACTIVEMQ_LIBS)\
#                       $(LOG4CXX_LIBS)

libxbe_la_SOURCES    = jsdl-schema.hpp jsdl-schema.cpp\
                       jsdl-posix-schema.hpp jsdl-posix-schema.cpp\
                       dsig-schema.hpp dsig-schema.cpp\
                       xenc-schema.hpp xenc-schema.cpp\
                       xbe-schema.hpp xbe-schema.cpp\
                       Task.hpp Task_sm.h Task_sm.cpp\
                       XbeLibUtils.hpp XbeLibUtils.cpp\
                       XbeException.hpp\
                       ChannelEventQueueAdapter.hpp ChannelEventQueueAdapter.cpp\
                       EventFactory.hpp EventFactory.cpp\
                       MessageEvent.hpp MessageEvent.cpp\
                       ErrorEvent.hpp ErrorEvent.cpp\
                       XMLMessageEvent.hpp XMLMessageEvent.cpp\
                       XMLSerializeStrategy.hpp XMLSerializeStrategy.cpp\
                       XMLDeserializeStrategy.hpp XMLDeserializeStrategy.cpp\
                       XMLMessageDispatcher.hpp

#libxbe_configdir     = $(libdir)/libxbe-@VERSION@/include
#libxbe_config_DATA   = $(top_srcdir)/config.h

libxbe_includedir      = $(includedir)/xbe-@VERSION@/xbe
libxbe_include_HEADERS = jsdl-schema.hpp\
                         jsdl-posix-schema.hpp\
                         dsig-schema.hpp\
                         xenc-schema.hpp\
                         xbe-schema.hpp\
                         Task.hpp Task_sm.h\
                         XbeLibUtils.hpp\
                         XbeException.hpp\
                         ChannelEventQueueAdapter.hpp\
                         EventFactory.hpp\
                         MessageEvent.hpp ErrorEvent.hpp\
                         XMLMessageEvent.hpp\
                         XMLSerializeStrategy.hpp XMLDeserializeStrategy.hpp

# remove auto generated files
maintainer-clean-local: remove-schema-bindings remove-fsm-files

remove-schema-bindings:
	-rm -f xbe-schema.hpp xbe-schema.cpp
	-rm -f jsdl-schema.hpp jsdl-schema.cpp
	-rm -f jsdl-posix-schema.hpp jsdl-posix-schema.cpp
	-rm -f xenc-schema.hpp xenc-schema.cpp
	-rm -f dsig-schema.hpp dsig-schema.cpp

remove-fsm-files:
	-rm -f Task_sm.h Task_sm.cpp

if HAVE_XSD_COMPILER

# provide schema to C++ generation support

xbe-schema.hpp xbe-schema.cpp: $(top_srcdir)/etc/xbe/schema/xbe-schema.xsd
	@$(XSD) cxx-tree --generate-serialization --hxx-suffix .hpp --cxx-suffix .cpp\
                --reserved-name "LINUX=LINUX_OS"\
                --namespace-map "http://www.xenbee.net/schema/2008/02/xbe=xbexsd"\
                --namespace-map "http://schemas.ggf.org/jsdl/2005/11/jsdl-posix=jsdlPosix"\
                --namespace-map "http://www.w3.org/2000/09/xmldsig#=dsig"\
                --namespace-map "http://www.w3.org/2001/04/xmlenc#=xenc"\
                --location-map "http://www.w3.org/TR/2002/REC-xmldsig-core-20020212/xmldsig-core-schema.xsd=dsig-schema.xsd"\
                --location-map "http://schemas.ggf.org/jsdl/2005/11/jsdl=jsdl-schema.xsd"\
                --location-map "http://www.w3.org/TR/2002/REC-xmlenc-core-20021210/xenc-schema.xsd=xenc-schema.xsd"\
                $<

jsdl-schema.hpp jsdl-schema.cpp: $(top_srcdir)/etc/xbe/schema/jsdl-schema.xsd
	@$(XSD) cxx-tree --generate-serialization --hxx-suffix .hpp --cxx-suffix .cpp\
                --reserved-name "LINUX=LINUX_OS"\
                --namespace-map "http://www.xenbee.net/schema/2008/02/xbe=xbexsd"\
                --namespace-map "http://schemas.ggf.org/jsdl/2005/11/jsdl-posix=jsdlPosix"\
                --namespace-map "http://www.w3.org/2000/09/xmldsig#=dsig"\
                --namespace-map "http://www.w3.org/2001/04/xmlenc#=xenc"\
                --location-map "http://www.w3.org/TR/2002/REC-xmldsig-core-20020212/xmldsig-core-schema.xsd=dsig-schema.xsd"\
                --location-map "http://schemas.ggf.org/jsdl/2005/11/jsdl=jsdl-schema.xsd"\
                --location-map "http://www.w3.org/TR/2002/REC-xmlenc-core-20021210/xenc-schema.xsd=xenc-schema.xsd"\
                --root-element-all\
                $<

jsdl-posix-schema.hpp jsdl-posix-schema.cpp: $(top_srcdir)/etc/xbe/schema/jsdl-posix-schema.xsd
	@$(XSD) cxx-tree --generate-serialization --hxx-suffix .hpp --cxx-suffix .cpp\
                --reserved-name "LINUX=LINUX_OS"\
                --namespace-map "http://www.xenbee.net/schema/2008/02/xbe=xbexsd"\
                --namespace-map "http://schemas.ggf.org/jsdl/2005/11/jsdl-posix=jsdlPosix"\
                --namespace-map "http://www.w3.org/2000/09/xmldsig#=dsig"\
                --namespace-map "http://www.w3.org/2001/04/xmlenc#=xenc"\
                --location-map "http://www.w3.org/TR/2002/REC-xmldsig-core-20020212/xmldsig-core-schema.xsd=dsig-schema.xsd"\
                --location-map "http://schemas.ggf.org/jsdl/2005/11/jsdl=jsdl-schema.xsd"\
                --location-map "http://www.w3.org/TR/2002/REC-xmlenc-core-20021210/xenc-schema.xsd=xenc-schema.xsd"\
                --root-element-all\
                $<

dsig-schema.hpp dsig-schema.cpp: $(top_srcdir)/etc/xbe/schema/dsig-schema.xsd
	@$(XSD) cxx-tree --generate-serialization --hxx-suffix .hpp --cxx-suffix .cpp\
                --reserved-name "LINUX=LINUX_OS"\
                --namespace-map "http://www.xenbee.net/schema/2008/02/xbe=xbexsd"\
                --namespace-map "http://schemas.ggf.org/jsdl/2005/11/jsdl-posix=jsdlPosix"\
                --namespace-map "http://www.w3.org/2000/09/xmldsig#=dsig"\
                --namespace-map "http://www.w3.org/2001/04/xmlenc#=xenc"\
                --location-map "http://www.w3.org/TR/2002/REC-xmldsig-core-20020212/xmldsig-core-schema.xsd=dsig-schema.xsd"\
                --location-map "http://schemas.ggf.org/jsdl/2005/11/jsdl=jsdl-schema.xsd"\
                --location-map "http://www.w3.org/TR/2002/REC-xmlenc-core-20021210/xenc-schema.xsd=xenc-schema.xsd"\
                --root-element-all\
                $<

xenc-schema.hpp xenc-schema.cpp: $(top_srcdir)/etc/xbe/schema/xenc-schema.xsd
	@$(XSD) cxx-tree --generate-serialization --hxx-suffix .hpp --cxx-suffix .cpp\
                --reserved-name "LINUX=LINUX_OS"\
                --namespace-map "http://www.xenbee.net/schema/2008/02/xbe=xbexsd"\
                --namespace-map "http://schemas.ggf.org/jsdl/2005/11/jsdl-posix=jsdlPosix"\
                --namespace-map "http://www.w3.org/2000/09/xmldsig#=dsig"\
                --namespace-map "http://www.w3.org/2001/04/xmlenc#=xenc"\
                --location-map "http://www.w3.org/TR/2002/REC-xmldsig-core-20020212/xmldsig-core-schema.xsd=dsig-schema.xsd"\
                --location-map "http://schemas.ggf.org/jsdl/2005/11/jsdl=jsdl-schema.xsd"\
                --location-map "http://www.w3.org/TR/2002/REC-xmlenc-core-20021210/xenc-schema.xsd=xenc-schema.xsd"\
                --root-element-all\
                $<

endif

# support for State Machine Compiler
if WITH_SMC
Task_sm.h Task_sm.cpp: Task.sm
	$(SMC) -c++ $<
endif

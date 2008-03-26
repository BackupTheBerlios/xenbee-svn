dnl
dnl AP_CHECK_LOG4CXX(minimal-version)
dnl
AC_DEFUN([AP_CHECK_LOG4CXX],
[
    AC_MSG_CHECKING(whether to disable logging)
    AC_ARG_ENABLE(logging,
        AC_HELP_STRING(
            [--disable-logging],
            [disable any logging performed via log4cxx (def=no)]
        ),
        disable_logging=yes,
        disable_logging=no
    )
    AC_MSG_RESULT($disable_logging)

    if test x"$disable_logging" = x"no" ; then
      log4cxx_version_min=$1
      AC_MSG_CHECKING(for Log4Cxx - version >= $log4cxx_version_min)
      PKG_CHECK_EXISTS(liblog4cxx >= $log4cxx_version_min,
  	[ # found
  	  AC_MSG_RESULT(yes)
  	  PKG_CHECK_MODULES(LOG4CXX, liblog4cxx >= $log4cxx_version_min)
  
          # check if log4cxx can be used
          ac_save_CXXFLAGS="$CXXFLAGS"
          ac_save_LDFLAGS="$LDFLAGS"
          CXXFLAGS="$CXXFLAGS $LOG4CXX_CFLAGS"
          LDFLAGS="$LOG4CXX_LIBS $LDFLAGS"
  
          AC_MSG_CHECKING(log4cxx usability)
          AC_LANG_PUSH([C++])
          AC_TRY_RUN([
#include <log4cxx/logger.h>
#include <log4cxx/basicconfigurator.h>
#include <log4cxx/helpers/exception.h>

using namespace log4cxx;
using namespace log4cxx::helpers;

LoggerPtr logger(Logger::getLogger("main"));

int
main()
{
   int result = 0;
   try {
     BasicConfigurator::configure();
   } catch (...) {
     result = 1;
   }
   return result;   
}
],disable_logging=no, disable_logging=yes, [])
          AC_LANG_POP([C++])
          CPPFLAGS="$ac_save_CPPFLAGS"
          LIBS="$ac_save_LIBS"
          
          if test x"$disable_logging" = x"no"; then
            AC_MSG_RESULT(yes)
	    AC_SUBST(LOG4CXX_CFLAGS)
            AC_SUBST(LOG4CXX_LIBS)
            AC_DEFINE(HAVE_LOG4CXX, 1, "Define if logging should be enabled")
          else
            disable_logging="yes"
            AC_MSG_ERROR(["*** A test application could not be linked with logging support.\n*** Support for logging has been disabled!"])
          fi
	],
	[ # not found
          disable_logging="yes"
          AC_MSG_WARN([the logging library could not be found])
	])
  fi
  AM_CONDITIONAL(BUILD_WITH_LOGGING, test x"$disable_logging" = x"no")
])

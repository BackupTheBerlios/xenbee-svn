dnl
dnl AP_CHECK_LOG4CXX(minimal-version)
dnl
AC_DEFUN([AP_CHECK_LOG4CXX],
[

AC_ARG_ENABLE(logging,
	[  --disable-logging  Disables any logging performed via log4cxx],
        [build_with_logging="no"])

  if test x$build_with_logging != xno ; then
    log4xx_version_min=$1
    AC_MSG_CHECKING(for Log4Cxx - version >= $log4cxx_version_min)
    PKG_CHECK_EXISTS(log4cxx >= $log4cxx_version_min,
	[ # found
	  AC_MSG_RESULT(yes)
	  PKG_CHECK_MODULES(LOG4CXX, log4cxx >= $log4cxx_version_min)
          AC_SUBST(LOG4CXX_CFLAGS)
          AC_SUBST(LOG4CXX_LIBS)
          AC_DEFINE(HAVE_LOG4XX, 1, "Define if logging should be enabled")
          build_with_logging="yes"
	],
	[ # not found
          build_with_logging="no"
          AC_MSG_RESULT(no)
	])
  fi
  AM_CONDITIONAL(BUILD_WITH_LOGGING, test "$build_with_logging" = yes)
])

dnl
dnl AP_CHECK_ACTIVEMQ(minimal-version)
dnl
AC_DEFUN([AP_CHECK_ACTIVEMQ],
[
  activemq_version_min=$1
  AC_MSG_CHECKING(for ActiveMQ - version >= $activemq_version_min)
  PKG_CHECK_EXISTS(activemq-cpp >= $activemq_version_min,
    [ # found
      AC_MSG_RESULT(yes)
      PKG_CHECK_MODULES(ACTIVEMQ, activemq-cpp >= $activemq_version_min)

      # check if activemq-cpp can be used
      ac_save_CXXFLAGS="$CXXFLAGS"
      ac_save_LDFLAGS="$LDFLAGS"
      CXXFLAGS="$CXXFLAGS $ACTIVEMQ_CFLAGS"
      LDFLAGS="$ACTIVEMQ_LIBS $LDFLAGS"

      AC_MSG_CHECKING(activemq-cpp usability)
      AC_LANG_PUSH([C++])
      AC_TRY_RUN([
#include <cms/Message.h>
#include <activemq/core/ActiveMQConnectionFactory.h>
#include <activemq/concurrent/Mutex.h>

int
main()
{
   activemq::concurrent::Mutex mtx;
   mtx.lock(); mtx.unlock();
   return 0;
}
],activemq_working="yes", activemq_working="no", [])
      AC_LANG_POP([C++])
      CPPFLAGS="$ac_save_CPPFLAGS"
      LIBS="$ac_save_LIBS"

      if test x$activemq_working != xno; then
        AC_MSG_RESULT(yes)
        AC_SUBST(ACTIVEMQ_CFLAGS)
        AC_SUBST(ACTIVEMQ_LIBS)
        AC_DEFINE(HAVE_ACTIVEMQ, 1, "Define if activemq is available")
      else
        AC_MSG_RESULT(no)
	echo "*** A test application could not be linked with activemq support."
	echo "*** Please make sure, that activemq works properly!"
	exit 1
      fi
    ],
    [ # not found
      activemq_working="no"
      AC_MSG_RESULT(no)
      exit 1
    ])
])

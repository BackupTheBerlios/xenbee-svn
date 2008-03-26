dnl
dnl AP_CHECK_CPPUNIT(minimal-version)
dnl
AC_DEFUN([AP_CHECK_CPPUNIT],
[
    AC_MSG_CHECKING(whether to build unit tests)
    AC_ARG_ENABLE(tests,
        AC_HELP_STRING(
            [--disable-tests],
            [disable unit tests (def=no)]
        ),
        unit_tests=no,
        unit_tests=yes
    )
    AC_MSG_RESULT($unit_tests)

    if test x"$unit_tests" = x"yes" ; then
      cppunit_version_min=$1
      AC_MSG_CHECKING(for CppUnit - version >= $cppunit_version_min)
      PKG_CHECK_EXISTS(cppunit >= $cppunit_version_min,
      [ # found
          AC_MSG_RESULT(yes)
          PKG_CHECK_MODULES(CPPUNIT, cppunit >= $cppunit_version_min)
          
          # check if cppunit can be used
          ac_save_CXXFLAGS="$CXXFLAGS"
          ac_save_LDFLAGS="$LDFLAGS"
          CXXFLAGS="$CXXFLAGS $CPPUNIT_CFLAGS"
          LDFLAGS="$CPPUNIT_LIBS $LDFLAGS"
          
          AC_MSG_CHECKING(cppunit usability)
          AC_LANG_PUSH([C++])
          AC_TRY_RUN([
#include <cppunit/ui/text/TestRunner.h>
int
main()
{
   CppUnit::TextUi::TestRunner runner;
   return 0;
}
],unit_tests=yes, unit_tests=no, [])
          AC_LANG_POP([C++])
          CPPFLAGS="$ac_save_CPPFLAGS"
          LIBS="$ac_save_LIBS"
          
          if test x"$unit_tests" = x"yes"; then
            AC_MSG_RESULT($unit_tests)
            AC_SUBST(CPPUNIT_CFLAGS)
            AC_SUBST(CPPUNIT_LIBS)
          else
            AC_MSG_RESULT($unit_tests)
          fi
	],
	[ # not found
          unit_tests=no
          AC_MSG_RESULT($unit_tests)
	])
  fi
  AM_CONDITIONAL(BUILD_UNIT_TESTS, test x"$unit_tests" = x"yes")
])


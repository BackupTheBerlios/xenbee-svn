dnl
dnl AP_CHECK_DEPRECATE_ATTR()
dnl
AC_DEFUN([AP_CHECK_DEPRECATE_ATTR],
[
    gcc_deprecated=yes
    AC_MSG_CHECKING([g++ deprecation attribute])
    AC_TRY_COMPILE(
       [void f() __attribute__ ((deprecated));],
       [],
       AC_DEFINE([HAVE_DEPRECATED_ATTRIBUTE],1,
		[Define if g++ supports deprecated attribute, as in g++ 4.0]),
       gcc_deprecated=no
    )
    AC_MSG_RESULT($gcc_deprecated)
])

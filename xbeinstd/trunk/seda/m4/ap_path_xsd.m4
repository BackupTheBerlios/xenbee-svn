dnl
dnl AP_PATH_XSD(MINIMUM-VERSION, [ACTION-IF-FOUND [, ACTION-IF-NOT-FOUND]])
dnl

AC_DEFUN([AP_PATH_XSD],
[
AC_ARG_WITH(xsd-prefix,
    AC_HELP_STRING(
        [--with-xsd-prefix=PFX],
        [Path to where xsd is installed (optional)]
    ),
    xsd_prefix="$withval",
    xsd_prefix="")

  if test x$xsd_prefix != x ; then
     if test x${XSD+set} != xset ; then
        XSD=$xsd_prefix/bin/xsd
     fi
  fi

  xsd_version_min=$1
  AC_PATH_PROG(XSD, xsd, no)
  AC_MSG_CHECKING(for CodeSynthesis XSD XML Schema to C++ compiler - version >= $xsd_version_min)
  have_xsd_compiler=no
  if test "$XSD" = "no" ; then
     AC_MSG_RESULT(no)
  else
     xsd_version=`${XSD} version 2>&1 | head -n 1 | sed 's/.*\([[[0-9]]]*\).\([[[0-9]]]*\).\([[[0-9]]]*\)/\1.\2.\3/'`
     xsd_major_version=`echo $xsd_version | sed 's/\([[[0-9]]]*\).\([[[0-9]]]*\).\([[[0-9]]]*\)/\1/'`
     xsd_minor_version=`echo $xsd_version | sed 's/\([[[0-9]]]*\).\([[[0-9]]]*\).\([[[0-9]]]*\)/\2/'`
     xsd_micro_version=`echo $xsd_version | sed 's/\([[[0-9]]]*\).\([[[0-9]]]*\).\([[[0-9]]]*\)/\3/'`

     xsd_major_min=`echo $xsd_version_min | sed 's/\([[[0-9]]]*\).\([[[0-9]]]*\).\([[[0-9]]]*\)/\1/'`
     if test "x${xsd_major_min}" = "x" ; then
        xsd_major_min=0
     fi

     xsd_minor_min=`echo $xsd_version_min | sed 's/\([[[0-9]]]*\).\([[[0-9]]]*\).\([[[0-9]]]*\)/\2/'`
     if test "x${xsd_minor_min}" = "x" ; then
        xsd_minor_min=0
     fi

     xsd_micro_min=`echo $xsd_version_min | sed 's/\([[[0-9]]]*\).\([[[0-9]]]*\).\([[[0-9]]]*\)/\3/'`
     if test "x${xsd_micro_min}" = "x" ; then
        xsd_micro_min=0
     fi
     xsd_version_match=`expr $xsd_major_version \>  $xsd_major_min \| \
                             $xsd_major_version \=  $xsd_major_min \& \
                             $xsd_minor_version \>  $xsd_minor_min \| \
                             $xsd_major_version \=  $xsd_major_min \& \
                             $xsd_minor_version \=  $xsd_minor_min \& \
                             $xsd_micro_version \>= $xsd_micro_min `
     if test "$xsd_version_match" = "1" ; then
        AC_MSG_RESULT(yes)
        have_xsd_compiler=yes
     else
        AC_MSG_RESULT(no)
        have_xsd_compiler=no
     fi
  fi

  if test "x$have_xsd_compiler" = x"no" ; then
     ifelse([$3], , :, [$3])
  else
     ifelse([$2], , :, [$2])
     AC_SUBST(XSD)
  fi
  AM_CONDITIONAL(HAVE_XSD_COMPILER, test x"$have_xsd_compiler" = x"yes")
])

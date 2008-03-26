dnl
dnl looks for the path of the State Machine Compiler (smc)
dnl
dnl AP_PATH_SMC([ACTION-IF-FOUND [, ACTION-IF-NOT-FOUND]])
dnl

AC_DEFUN([AP_PATH_SMC],
[
AC_ARG_WITH(smc,
    AC_HELP_STRING(
        [--with-smc=PFX],
        [Path to where smc is installed (optional)]
    ),
    smc_prefix="$withval",
    smc_prefix="${SMC_HOME}")

  if test x$smc_prefix != x ; then
     if test x${SMC+set} != xset ; then
        SMC="java -jar $smc_prefix/bin/Smc.jar"
     fi
  fi
  SMC_HOME=$smc_prefix
  AC_MSG_CHECKING([for State Machine Compiler (smc)])

  have_smc=no
  if test -f "$SMC_HOME/lib/statemap.jar" -a -f "$SMC_HOME/bin/Smc.jar" ; then
     have_smc=yes
  fi
  AC_MSG_RESULT($have_smc)

  if test "x$have_smc" = x"no" ; then
     ifelse([$2], , :, [$2])
     HAVE_SMC="no"
  else
     ifelse([$1], , :, [$1])
     SMC_CFLAGS="-I${SMC_HOME}/lib"
     AC_SUBST(SMC)
     AC_SUBST(SMC_HOME)
     AC_SUBST(SMC_CFLAGS)
     HAVE_SMC="yes"
  fi
  AM_CONDITIONAL(WITH_SMC, test x"$have_smc" = x"yes")
])

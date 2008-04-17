# Code taken from Martin Mann "mmann <at> informatik <dot> uni-freiburg <dot> de"
#
# Src: http://www.bioinf.uni-freiburg.de/~mmann/HowTo/automake.html#debug
# 

AC_DEFUN([AP_CHECK_DEBUG],
[
    # add checking message
    AC_MSG_CHECKING(whether to build with debug information)
    
    # create configure parameter and init variable $debuger
    debuger=no
    AC_ARG_ENABLE(debug,
    	AC_HELP_STRING(
    	    [--enable-debug],
    	    [enable debug data generation (def=no)]
    	),
      	debuger="$enableval"
    )
    
    # resulting value to screen (to complete checking message)
    AC_MSG_RESULT($debuger)
    
    # set DEBUG flag and introduce additional compiler flags
    if test x"$debuger" = x"yes"; then
    	AC_DEFINE(DEBUG)
    	CXXFLAGS="$CXXFLAGS -g -Wall -Werror"
    fi
])

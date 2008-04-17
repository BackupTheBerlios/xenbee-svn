#if HAVE_CONFIG_H
#  include <config.h>
#endif

#include "common.h"
#include "error.h"

static void error (int exit_status, const char *mode, 
		                   const char *message);

static void
error (int exit_status, const char *mode, const char *message)
{
    fprintf (stderr, "%s: %s.\n", mode, message);

    if (exit_status >= 0)
        exit (exit_status);
}

void
mqs_warning (const char *message)
{
    error (-1, "W", message);
}

void
mqs_error (const char *message)
{
    error (-1, "E", message);
}

void
mqs_fatal (const char *message)
{
    error (EXIT_FAILURE, "F", message);
}


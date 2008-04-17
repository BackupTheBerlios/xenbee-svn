#ifndef MQS_ERROR_H
#define MQS_ERROR_H 1

/*
 * Provides some error handling functions.
 */
#include <mqs/common.h>

BEGIN_C_DECLS

extern void mqs_warning      (const char *message);
extern void mqs_error        (const char *message);
extern void mqs_fatal        (const char *message);

END_C_DECLS

#endif /* !MQS_ERROR_H */

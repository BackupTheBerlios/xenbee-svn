#ifndef MQS_DEPRECATE_HPP
#define MQS_DEPRECATE_HPP 1

#ifdef HAVE_CONFIG_H
#include <mqs/config.h>
#endif

#ifdef HAVE_DEPRECATE_ATTRIBUTE
#define DEPRECATED_API __attribute__ ((deprecated))
#else
#define DEPRECATED_API
#endif

#endif // !MQS_DEPRECATE_HPP

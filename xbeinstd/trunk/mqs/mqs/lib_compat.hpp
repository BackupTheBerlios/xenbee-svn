#ifndef MQS_WIN_COMPAT_HPP
#define MQS_WIN_COMPAT_HPP 1

#ifdef MQS_WINDOWS

BEGIN_C_DECLS
extern int getpid();
END_C_DECLS

#endif

#endif

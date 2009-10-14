/*
 * =====================================================================================
 *
 *       Filename:  memory.hpp
 *
 *    Description:  define shared_ptr
 *
 *        Version:  1.0
 *        Created:  10/14/2009 02:11:52 PM
 *       Revision:  none
 *       Compiler:  gcc
 *
 *         Author:  Alexander Petry (petry), alexander.petry@itwm.fraunhofer.de
 *        Company:  Fraunhofer ITWM
 *
 * =====================================================================================
 */

#ifndef MQS_MEMORY_HPP
#define MQS_MEMORY_HPP 1

#ifdef HAVE_CONFIG_H
#  include <config.h>
#endif

#if defined(USE_STL_TR1) && (USE_STL_TR1 == 1)
#  include <tr1/memory>
#else
#  include <boost/tr1/memory.hpp>
#endif

namespace mqs
{
  using ::std::tr1::shared_ptr;
}

#endif

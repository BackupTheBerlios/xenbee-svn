/* 
   Copyright (C) 2009 Alexander Petry <alexander.petry@itwm.fraunhofer.de>.

   This file is part of seda.

   seda is free software; you can redistribute it and/or modify it
   under the terms of the GNU General Public License as published by the
   Free Software Foundation; either version 2, or (at your option) any
   later version.

   seda is distributed in the hope that it will be useful, but WITHOUT
   ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
   FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
   for more details.

   You should have received a copy of the GNU General Public License
   along with seda; see the file COPYING.  If not, write to
   the Free Software Foundation, Inc., 59 Temple Place - Suite 330,
   Boston, MA 02111-1307, USA.  

*/

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

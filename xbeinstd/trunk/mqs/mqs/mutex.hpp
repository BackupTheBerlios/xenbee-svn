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

#ifndef MQS_MUTEX_HPP
#define MQS_MUTEX_HPP 1

#ifdef USE_ACTIVE_MQ_2_2_1
#include <decaf/util/concurrent/Synchronizable.h>
#include <decaf/util/concurrent/Mutex.h>
#include <decaf/util/concurrent/CountDownLatch.h>
#include <decaf/util/concurrent/Lock.h>
#define MQS_CONCURRENT_NS decaf::util::concurrent
#else
#include <activemq/concurrent/Synchronizable.h>
#include <activemq/concurrent/Mutex.h>
#include <activemq/concurrent/CountDownLatch.h>
#include <activemq/concurrent/Lock.h>
#define MQS_CONCURRENT_NS activemq::concurrent
#endif

namespace mqs {
    typedef MQS_CONCURRENT_NS::Mutex Mutex;
    typedef MQS_CONCURRENT_NS::Synchronizable Synchronizable;
    typedef MQS_CONCURRENT_NS::CountDownLatch Semaphore;
    typedef MQS_CONCURRENT_NS::Lock Lock;
}

#undef MQS_CONCURRENT_NS

#endif

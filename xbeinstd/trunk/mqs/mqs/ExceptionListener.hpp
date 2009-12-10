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

#ifndef MQS_EXCEPTION_LISTENER_HPP
#define MQS_EXCEPTION_LISTENER_HPP 1

#include <cms/CMSException.h>
#include <mqs/MQSException.hpp>

namespace mqs {
    class ExceptionListener {
    public:
        virtual void onException(const cms::CMSException &) = 0;
        virtual void onException(const mqs::MQSException &) = 0;
    };
}

#endif // ! MQS_MESSAGE_LISTENER_HPP

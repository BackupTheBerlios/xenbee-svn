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

#ifndef MQS_RESPONSE_HPP
#define MQS_RESPONSE_HPP

#include <cassert>
#include <boost/thread.hpp>

#include <mqs/Message.hpp>

namespace mqs {
    /**
      This class fulfills the following purpose:

      If a thread  places a request (send with reply),  a new object of
      this  class  is  kept  to  be  able  to  keep  track  of  waiting
      threads. When  a new message  arrives, the waiting  responses are
      scanned and the appropriate thread is notified.

      Thus this class holds three values:
      - a countdown latch (actually a semaphore) on which a thread waits
      - the correlation id (checked against arriving messages)
      - a pointer to the response message (filled by the receiver)
      */
    class Response {
        public:
            Response(const std::string& id)
                : response((mqs::Message*)NULL), correlationID(id) {}

            void await() {
                boost::unique_lock<boost::mutex> lock(_mtx);
                while (! response) {
                    _cond.wait(lock);
                }
            }
            void await(unsigned long millis) {
                boost::unique_lock<boost::mutex> lock(_mtx);
                while (! response) {
                    boost::system_time const timeout=boost::get_system_time() + boost::posix_time::milliseconds(millis);
                    if (! _cond.timed_wait(lock, timeout)) {
                        break;
                    }
                }
            }

            void setResponse(mqs::Message::Ptr r) {
                boost::unique_lock<boost::mutex> lock(_mtx);
                assert(response.get() == NULL);
                response = r;
                // wake up the request-sender
                _cond.notify_one();
            }

            const std::string& getCorrelationID() const { return correlationID; }
            mqs::Message::Ptr getResponse() { return response; }
            bool timedout() const { return response.get() == NULL; }
        private:
            mqs::Message::Ptr response;
            const std::string correlationID;
            boost::mutex _mtx;
            boost::condition_variable _cond;
    };
}

#endif // !MQS_RESPONSE_HPP

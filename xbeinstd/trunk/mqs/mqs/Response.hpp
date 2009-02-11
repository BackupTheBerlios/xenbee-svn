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

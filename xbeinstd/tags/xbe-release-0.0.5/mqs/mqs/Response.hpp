#ifndef MQS_RESPONSE_HPP
#define MQS_RESPONSE_HPP

#include <cassert>

#include <cms/Message.h>
#include <mqs/mutex.hpp>

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
      : response(NULL), correlationID(id), semaphore(1) {}

    void await(unsigned long millisec = 0xffffffff) { semaphore.await(millisec); }

    void setResponse(cms::Message* r) {
      assert(response == NULL);
      response = r;
      // wake up the request-sender
      semaphore.countDown();
    }

    const std::string& getCorrelationID() const { return correlationID; }
    cms::Message* getResponse() { return response; }
    bool timedout() const { return response == NULL; }
  private:
    cms::Message* response;
    const std::string correlationID;
    Semaphore semaphore;
  };
}

#endif // !MQS_RESPONSE_HPP

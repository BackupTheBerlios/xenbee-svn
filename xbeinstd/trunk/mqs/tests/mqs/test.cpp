#include <mqs/common.h>
#include <mqs/error.h>

#include <mqs/Response.hpp>
#include <mqs/Destination.hpp>
#include <mqs/Channel.hpp>

#include <cms/TextMessage.h>
#include <activemq/concurrent/Thread.h>
#include <iostream>

#if HAVE_LOG4CXX
#include <log4cxx/basicconfigurator.h>
#endif

class Pinger : public activemq::concurrent::Thread {
public:
  Pinger(mqs::Channel* channel, const mqs::Destination& ponger, int count = 1)
    : _channel(channel), _ponger(ponger), _count(count), _status(0) {}
  ~Pinger() {}

  void run() {
    DEFINE_LOGGER("pinger");
    LOG_INFO("starting");
    
    for (int i = 0; i < _count; ++i) {
      try {
	LOG_INFO("ping");
	cms::TextMessage* reply(static_cast<cms::TextMessage*>(_channel->request("ping" /*, _ponger*/, 100)));
	if (reply) {
	  LOG_INFO(reply->getText());
	  _status = 2; // ok
	  delete reply;
	} else {
	  LOG_WARN("failed");
	  _status = 1;
	}
      } catch (std::exception& e) {
	LOG_ERROR("send failed: " << e.what());
	_status = 1;
      }
    }
    LOG_INFO("done.");
    *_channel << "done";
  }

public:
  int getStatus() const { return _status; }
  
private:
  mqs::Channel* _channel;
  mqs::Destination _ponger;
  int _count;
  int _status;
};

class Ponger : public activemq::concurrent::Thread {
public:
  Ponger(mqs::Channel* channel)
    : _channel(channel), _retries(10), _status(0) {}
  ~Ponger() {}

  void run() {
    DEFINE_LOGGER("ponger");
    LOG_INFO("starting");

    for (; _retries > 0 ;) {
      cms::TextMessage* msg(static_cast<cms::TextMessage*>(_channel->recv(100)));
      if (msg) {
	if (msg->getText() == "done") {
	  LOG_INFO("done.");
	  _retries = 0;
	  _status = 2; // ok
	} else {
	  try {
	    _channel->reply(msg, "pong");
	  } catch (std::exception& e) {
	    LOG_ERROR("reply failed: " << e.what());
	    _status = 0;
	  }
	}
      } else {
	LOG_INFO("no incoming message");
	_status = 1;
	_retries--;
      }
    }
  }

public:
  int getStatus() const { return _status; }

  mqs::Channel* _channel;
  int _retries;
  int _status; // 0 - unkown 1 - failed 2 - ok
};

int main (int argc, char** argv) {
  DEFINE_LOGGER("main");
  
  try {
    mqs::Destination d("foo.bar?k1=v1&k2=v2&type=queue");
    LOG_INFO("destination: " << d.str());
  } catch (const std::exception& e) {
    LOG_FATAL("exception: " << e.what());
    exit(EXIT_FAILURE);
  }

  try {
    const std::string pingerQueue("foo.bar.pinger?timeToLive=100&type=queue");
    const std::string pongerQueue("foo.bar.ponger?timeToLive=100&type=queue");
    
    mqs::Channel pi2po(mqs::BrokerURI("tcp://localhost:61616"),
		       mqs::Destination(pingerQueue),
		       mqs::Destination(pongerQueue));
    
    mqs::Channel po2pi(mqs::BrokerURI("tcp://localhost:61616"),
		       mqs::Destination(pongerQueue),
		       mqs::Destination(pingerQueue));
    
    pi2po.start();
    po2pi.start();

    Ponger ponger(&po2pi); // uses reply
    Pinger pinger(&pi2po, mqs::Destination(pongerQueue), 5);

    ponger.start();
    pinger.start();

    pinger.join();
    ponger.join();

    // check final states
    if ((pinger.getStatus() != 2) || (ponger.getStatus() != 2)) {
      std::cerr << "Ping/Pong Test failed: states: pinger("<<
	pinger.getStatus()<< ") ponger(" << ponger.getStatus() << ")" << std::endl;
      exit(1);
    }

    /*    
    // Send a simple test
    cms::TextMessage *msg1 = c.createTextMessage("Hello World!");
    c.send(msg1);
    std::cerr << "sent: " << msg1->getCMSMessageID() << std::endl;
    cms::TextMessage *msg = static_cast<cms::TextMessage*>(c.recv(1000));
    if (msg) {
      std::cerr << "got: " << msg->getText() << std::endl;
      std::cerr << msg->getCMSMessageID() << std::endl;
    } else {
      throw std::runtime_error("send/recv failed");
    }
    delete msg; msg = NULL;
    */
    
  } catch (const std::exception& e) {
    LOG_FATAL("exception: " << e.what());
    exit(EXIT_FAILURE);
  } catch (...) {
    LOG_FATAL("unknown exception");
    exit(EXIT_FAILURE);
  }

  exit(EXIT_SUCCESS);
}

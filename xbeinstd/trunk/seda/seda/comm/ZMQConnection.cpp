#include "ZMQConnection.hpp"

#include <unistd.h>
#include <utility> // std::make_pair

using namespace seda::comm;

ZMQConnection::ZMQConnection(const std::string &locator, const std::string &name, const std::string &in_interface, const std::string &out_interface)
  : locator_host_(locator),
    name_(name),
    in_iface_(in_interface),
    out_iface_(out_interface),
    dispatcher_(0),
    locator_(0),
    io_thread_(0),
    api_(0),
    incoming_queue_(-1)
{}

ZMQConnection::~ZMQConnection() {
  try {
    stop();
  } catch(...) {
    // ignore
  }
}

void ZMQConnection::start() {
  assert(dispatcher_ == 0);
  assert(locator_ == 0);
  assert(io_thread_ == 0);
  assert(api_ == 0);

  dispatcher_ = new zmq::dispatcher_t(2);
  locator_ = new zmq::locator_t(locator_host_.c_str());
  io_thread_ = zmq::io_thread_t::create(dispatcher_);
  api_ = zmq::api_thread_t::create(dispatcher_, locator_);
  std::string qname(std::string("Q_") + name_);
  incoming_queue_ = api_->create_queue(qname.c_str(), zmq::scope_global, in_iface_.c_str(), io_thread_, 1, &io_thread_);
}

void ZMQConnection::stop() {
  if (dispatcher_) {
    delete dispatcher_;
  }
  if (locator_) {
    delete locator_;
  }
  dispatcher_ = 0;
  locator_ = 0;
  io_thread_ = 0;
  api_ = 0;
  incoming_queue_ = -1;

  sleep(1);
}

void ZMQConnection::send(const seda::comm::SedaMessage &msg) {
  std::string encodedMsg(msg.encode());

  zmq::message_t m((void*)encodedMsg.data(), encodedMsg.size(), 0);
  exchange_t eid = locate(msg.to());

  api_->send(eid, m);
}

ZMQConnection::exchange_t ZMQConnection::locate(const SedaMessage::address_type &addr) {
  exchange_t eid = -1;
  address_map_t::iterator it(exchanges_.find(addr));
  if (it == exchanges_.end()) {
    std::string xname(std::string("E_") + addr);
    std::string qname(std::string("Q_") + addr);
    eid = api_->create_exchange(xname.c_str());
    api_->bind(xname.c_str(), qname.c_str(), NULL, io_thread_);
    exchanges_.insert(std::make_pair(addr, eid));
  } else {
    eid = it->second;
  }
  return eid;
}

int ZMQConnection::receive(SedaMessage &msg, bool block) {
  zmq::message_t m;
  const int code = api_->receive(&m, block);
  if (code == incoming_queue_) {
    // message seems to be ok
    std::string data((const char*)m.data(), m.size());
    msg.decode(data);
  }
  return code;
}

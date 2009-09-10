#include "ZMQConnection.hpp"

#include <unistd.h>
#include <utility> // std::make_pair
#include <sstream>
#include <iomanip>

using namespace seda::comm;

ZMQConnection::ZMQConnection(
    const std::string &locator
  , const std::string &name
  , const std::string &in_interface
  , const std::string &out_interface)
  : locator_host_(locator)
  , name_(name)
  , in_iface_(in_interface)
  , out_iface_(out_interface)
  , dispatcher_(0)
  , locator_(0)
  , io_thread_(0)
  , send_api_(0)
  , recv_api_(0)
  , incoming_queue_(-1)
  , self_exchange_(-1)
  , recv_waiting_(0)
{
}

ZMQConnection::~ZMQConnection()
{
  try {
    stop();
  } catch(...) {
    // ignore
  }
}

void ZMQConnection::start()
{
  boost::unique_lock<boost::recursive_mutex> lock(mtx_);
  std::cerr << "starting connection..." << std::endl;
  if (dispatcher_ != 0)
    return;

  assert(dispatcher_ == 0);
  assert(locator_ == 0);
  assert(io_thread_ == 0);
  assert(send_api_ == 0);
  assert(recv_api_ == 0);

  dispatcher_ = new zmq::dispatcher_t(3);
  locator_ = new zmq::locator_t(locator_host_.c_str());
  io_thread_ = zmq::poll_thread_t::create(dispatcher_);
  send_api_ = zmq::api_thread_t::create(dispatcher_, locator_);
  recv_api_ = zmq::api_thread_t::create(dispatcher_, locator_);

  std::string qname(std::string("Q_") + name_);
  incoming_queue_ = recv_api_->create_queue(qname.c_str()
                                     , zmq::scope_global
                                     , in_iface_.c_str()
                                     , io_thread_
                                     , 1
                                     , &io_thread_);
  self_exchange_ = locate(name_);

  std::cerr << "registered " << qname << " with zmq: " << incoming_queue_ << " and exchange to self: " << self_exchange_ << std::endl;

  // initialize the receive thread
  recv_thread_ = new boost::thread(boost::ref(*this));

  std::cerr << "connection started up" << std::endl;
}

void ZMQConnection::stop()
{
  boost::unique_lock<boost::recursive_mutex> lock(mtx_);
  std::cerr << "stopping connection" << std::endl;
  if (dispatcher_ == 0) return;

  {
    recv_thread_->interrupt();
    std::cerr << "interrupted thread" << std::endl;
    zmq::message_t m(10);
    send_api_->send(self_exchange_, m);
    recv_thread_->join();
    std::cerr << "joined thread" << std::endl;
  }

  if (recv_thread_)
  {
    delete recv_thread_;
    recv_thread_ = 0;
    std::cerr << "thread deleted" << std::endl;
  }

  if (locator_)
  {
    delete locator_;
    locator_ = 0;
  }

  if (dispatcher_)
  {
    delete dispatcher_;
    dispatcher_ = 0;
  }

  io_thread_ = 0;
  send_api_ = 0;
  recv_api_ = 0;
  incoming_queue_ = -1;
  self_exchange_ = -1;
  exchanges_.clear();

  std::cerr << "connection shut down" << std::endl;
}

void ZMQConnection::operator()()
{
  // thread entry function
  for (;;)
  {
    zmq::message_t m;
    int code;

    std::cerr << "api->receive()" << std::endl;
    // FIXME: I don't see a way how to avoid polling here
    // when i choose 'true' the api->send and api->receive calls don't play together ;-(
    // when i create new api-thread for this thread, i get a failed assertion ;-(

    {
      code = recv_api_->receive(&m, true);
      std::cerr << "api->receive() returned: " << code << std::endl;
      try {
        boost::this_thread::interruption_point();
      } catch (const boost::thread_interrupted &irq) {
        std::cerr << "interrupted" << std::endl;
        break;
      }
    }

    if (code == incoming_queue_)
    {
      // message seems to be ok
      std::string data((const char*)m.data(), m.size());
      {
        std::stringstream sstr;
        sstr << std::hex << std::right;
        for (std::size_t i(0); i < m.size(); ++i) {
           int c = (int(((const char*)m.data())[i]) & 0xff);
           sstr << std::setw(2) << std::setfill('0') << c;
        }
        std::cerr << "got message: " << sstr.str() << std::endl;
      }

      seda::comm::SedaMessage msg;
      try {
        msg.decode(data);
      } catch (...) {
        continue;
      }

      if (listener_list_.empty())
      {
        boost::unique_lock<boost::recursive_mutex> lock(mtx_);
        std::cerr << "enqueueing message " << std::endl;
        incoming_messages_.push_back(msg);
        recv_cond_.notify_one();
      }
      else
      {
        if (recv_waiting_)
        {
          boost::unique_lock<boost::recursive_mutex> lock(mtx_);
          std::cerr << "enqueueing message " << std::endl;
          incoming_messages_.push_back(msg);
          recv_cond_.notify_one();
        }
        else
        {
          std::cerr << "notifying listener processes" << std::endl;
          notifyListener(msg);
        }
      }
    }
  }
  std::cerr << "recv thread shut down" << std::endl;
}

void ZMQConnection::send(const seda::comm::SedaMessage &msg)
{
  const std::string encodedMsg(msg.encode());

  zmq::message_t m(encodedMsg.size());
  memcpy(m.data(), encodedMsg.data(), encodedMsg.size());
  exchange_t eid = locate(msg.to());

  boost::unique_lock<boost::recursive_mutex> lock(mtx_);
  std::cerr << "api->send("<<eid<<", " << msg.str() << ")" << std::endl;
  send_api_->send(eid, m);
}

ZMQConnection::exchange_t ZMQConnection::locate(const SedaMessage::address_type &addr)
{
  boost::unique_lock<boost::recursive_mutex> lock(mtx_);
  exchange_t eid = -1;
  address_map_t::iterator it(exchanges_.find(addr));
  if (it == exchanges_.end())
  {
    std::string xname(std::string("E_") + addr);
    std::string qname(std::string("Q_") + addr);
    std::cerr << "creating exchange between " << xname << " and " << qname << std::endl;
    eid = send_api_->create_exchange(xname.c_str());
    send_api_->bind(xname.c_str(), qname.c_str(), io_thread_, io_thread_);
    exchanges_.insert(std::make_pair(addr, eid));
  }
  else
  {
    eid = it->second;
  }
  return eid;
}

template <typename T> struct recv_waiting_mgr {
  recv_waiting_mgr(T *cnt) : cnt(cnt) { *cnt++; }
  ~recv_waiting_mgr() { *cnt--; }
  T *cnt;
};

bool ZMQConnection::recv(SedaMessage &msg, const bool block) throw(boost::thread_interrupted)
{
  boost::unique_lock<boost::recursive_mutex> lock(mtx_);

  recv_waiting_mgr<std::size_t> waiting_mgr(&recv_waiting_);

  std::cerr << "conn->recv()" << std::endl;
  if (block)
  {
    while (incoming_messages_.empty())
    {
      recv_cond_.wait(lock);
    }

    msg = incoming_messages_.front();
    incoming_messages_.pop_front();
    std::cerr << "got message: " << msg.str() << std::endl;
    return true;
  }
  else
  {
    if (incoming_messages_.empty())
    {
      return false;
    }
    else
    {
      msg = incoming_messages_.front();
      incoming_messages_.pop_front();
      return true;
    }
  }
}


#ifndef SEDA_COMM_ZMQ_CONNECTION_HPP
#define SEDA_COMM_ZMQ_CONNECTION_HPP 1

#include <map>
#include <string>
#include <seda/comm/Encodeable.hpp>
#include <seda/comm/SedaMessage.hpp>

#include <zmq.hpp>

namespace seda {
namespace comm {
  class ConnectionListener {
  public:
    virtual void onMessage(const seda::comm::SedaMessage::Ptr &) = 0;
  };

  class Connection {
  public:
    virtual void start() = 0;
    virtual void stop() = 0;

    virtual void send(const seda::comm::SedaMessage::Ptr &) = 0;
  };

  class ZMQConnection {
  public:
    typedef int exchange_t;
    typedef int queue_t;
    typedef std::map<SedaMessage::address_type, exchange_t> address_map_t;

    ZMQConnection(const std::string &locator, const std::string &name, const std::string &in_interface, const std::string &out_interface);
    ~ZMQConnection();

    void start();
    void stop();

    void send(const seda::comm::SedaMessage &);
    int receive(seda::comm::SedaMessage &m, bool block = true);

  protected:
    exchange_t locate(const SedaMessage::address_type &);
  private:
    std::string locator_host_;
    std::string name_;
    std::string in_iface_;
    std::string out_iface_;

    zmq::dispatcher_t dispatcher_;
    zmq::locator_t locator_;
    zmq::i_thread *io_thread_;
    zmq::api_thread_t *api_;

    queue_t incoming_queue_;
    address_map_t exchanges_;
  };
}
}

#endif

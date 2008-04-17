#ifndef MQS_BROKER_URI_HPP
#define MQS_BROKER_URI_HPP

#include <string>

namespace mqs {  
  class BrokerURI {
  public:
    explicit
    BrokerURI(const std::string& uri)
      : value(uri) {}
  public:
    const std::string value;
  };
}

#endif // !MQS_BROKER_URI_HPP

#ifndef MQS_DESTINATIONPROPERTIES_HPP
#define MQS_DESTINATIONPROPERTIES_HPP 1

#include <string>

namespace mqs {
  class DestinationProperties {
  public:
    ~DestinationProperties() {}

    class Property {
    public:
      Property(const std::string& n, const std::string& d) : name(n), def(d) {}
      const std::string name;
      const std::string def;
    };
    
    static const Property TYPE;
  };
}

#endif // !MQS_DESTINATIONPROPERTIES_HPP

#ifndef XBE_ERROREVENT_HPP
#define XBE_ERROREVENT_HPP 1

#include <seda/IEvent.hpp>

namespace xbe {
  class ErrorEvent : public seda::IEvent {
  public:
    ErrorEvent(const std::string& reason, const std::string& additionalData="");
    ~ErrorEvent();

    const std::string& reason() const;
    const std::string& additionalData() const;
    
    std::string str() const;
  private:
    std::string _reason;
    std::string _additionalData;
  };
}

#endif // !XBE_MESSAGEEVENT_HPP

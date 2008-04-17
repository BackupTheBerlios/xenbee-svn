#ifndef XBE_MESSAGEEVENT_HPP
#define XBE_MESSAGEEVENT_HPP 1

#include <cms/Message.h>
#include <mqs/Destination.hpp>
#include <seda/IEvent.hpp>

namespace xbe {
  class MessageEvent : public seda::IEvent {
  public:
    MessageEvent(const std::string& msg);
    MessageEvent(const std::string& msg, const mqs::Destination& src);
    MessageEvent(const std::string& msg, const mqs::Destination& src, const mqs::Destination& dst);
    ~MessageEvent();

    const std::string& message() const { return _msg; }
    const std::string& id() const { return _id; }
    void id(const std::string& id) { _id = id; }
    
    const mqs::Destination& source() const { return _src; }
    const mqs::Destination& destination() const { return _dst; }
    void destination(const mqs::Destination& d) { _dst = d; }

    std::string str() const;
  private:
    std::string _msg;
    std::string _id;
    mqs::Destination _src;
    mqs::Destination _dst;
  };
}

#endif // !XBE_MESSAGEEVENT_HPP

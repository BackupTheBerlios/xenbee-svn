#ifndef XBE_XML_MESSAGEEVENT_HPP
#define XBE_XML_MESSAGEEVENT_HPP 1

#include <seda/IEvent.hpp>
#include <xbe/xbe-schema.hpp>

namespace xbe {
  class XMLMessageEvent : public seda::IEvent {
  public:
    //    typedef std::auto_ptr<xbexsd::message> MsgPtr;
    
    XMLMessageEvent(const xbexsd::message_t&);
    virtual ~XMLMessageEvent() {}

    virtual std::string str() const;
    const xbexsd::message_t& message() const { return _msg; }
    void message(const xbexsd::message_t& m) { _msg = m; }
  private:
    xbexsd::message_t _msg;
  };
}

#endif // !XBE_XML_MESSAGEEVENT_HPP

#ifndef XBE_XML_MESSAGEEVENT_HPP
#define XBE_XML_MESSAGEEVENT_HPP 1

#include <seda/IEvent.hpp>
#include <xbe/xbe-msg.hpp>

namespace xbe {
  class XMLMessageEvent : public seda::IEvent {
  public:
    //    typedef std::auto_ptr<xbexsd::message> MsgPtr;
    
    XMLMessageEvent(const xbemsg::message_t&);
    virtual ~XMLMessageEvent() {}

    virtual std::string str() const;
    const xbemsg::message_t& message() const { return _msg; }
    void message(const xbemsg::message_t& m) { _msg = m; }
  private:
    xbemsg::message_t _msg;
  };
}

#endif // !XBE_XML_MESSAGEEVENT_HPP

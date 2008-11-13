#ifndef XBE_XML_MESSAGEEVENT_HPP
#define XBE_XML_MESSAGEEVENT_HPP 1

#include <seda/UserEvent.hpp>
#include <xbe/xbe-msg.hpp>

namespace xbe {
    namespace event {
        class XMLMessageEvent : public seda::UserEvent {
            public:
                XMLMessageEvent(const xbemsg::message_t&);
                virtual ~XMLMessageEvent() {}

                virtual std::string str() const;
                const xbemsg::message_t& message() const { return *_msg; }
                xbemsg::message_t& message() { return *_msg; }
                void message(const xbemsg::message_t& m);
            private:
                std::auto_ptr<xbemsg::message_t> _msg;
        };
    }
}

#endif // !XBE_XML_MESSAGEEVENT_HPP

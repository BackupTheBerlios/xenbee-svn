#ifndef XBE_XBEINSTD_EVENT_HPP
#define XBE_XBEINSTD_EVENT_HPP 1

#include <seda/UserEvent.hpp>

namespace xbe {
    namespace event {
        class XbeInstdEvent : public seda::UserEvent {
            public:
                XbeInstdEvent(const std::string &to, const std::string &from, const std::string &conversationID)
                : _to(to), _from(from), _conversationID(conversationID) {}
                virtual ~XbeInstdEvent() {}

                virtual std::string str() const = 0;

                virtual const std::string & conversationID() const { return _conversationID; }
                virtual const std::string & from() const { return _from; }
                virtual const std::string & to() const { return _to; }
            private:
                std::string _to;
                std::string _from;
                std::string _conversationID;
        };
    }
}

#endif // !XBE_XBEINSTD_EVENT_HPP

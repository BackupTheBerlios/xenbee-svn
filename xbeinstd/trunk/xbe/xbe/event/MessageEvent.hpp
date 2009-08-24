#ifndef XBE_MESSAGEEVENT_HPP
#define XBE_MESSAGEEVENT_HPP 1

#include <mqs/Destination.hpp>
#include <seda/UserEvent.hpp>

namespace xbe {
    namespace event {
        class MessageEvent : public seda::UserEvent {
            public:
                MessageEvent(const std::string& msg);
                MessageEvent(const std::string& msg, const mqs::Destination& dst, const mqs::Destination& src);
                virtual ~MessageEvent();

                const std::string& message() const { return _msg; }
                const std::string& id() const { return _id; }
                void id(const std::string& id) { _id = id; }

                const mqs::Destination& source() const { return _src; }
                const mqs::Destination& destination() const { return _dst; }
                void source(const mqs::Destination& s) { _src = s; }
                void destination(const mqs::Destination& d) { _dst = d; }

                std::string str() const;
            private:
                std::string _msg;
                std::string _id;
                mqs::Destination _dst;
                mqs::Destination _src;
        };
    }
}

#endif // !XBE_MESSAGEEVENT_HPP

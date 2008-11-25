#ifndef XBE_LIFE_SIGN_EVENT_HPP
#define XBE_LIFE_SIGN_EVENT_HPP 1

#include <xbe/event/XbeInstdEvent.hpp>

namespace xbe {
    namespace event {
        class LifeSignEvent : public xbe::event::XbeInstdEvent {
            public:
                LifeSignEvent(const std::string &to, const std::string &from, const std::string &conversationID)
                : xbe::event::XbeInstdEvent(to, from, conversationID) {}
                virtual ~LifeSignEvent() {}

                virtual std::string str() const {return "life-sign";}
        };
    }
}

#endif // !XBE_LIFE_SIGN_EVENT_HPP

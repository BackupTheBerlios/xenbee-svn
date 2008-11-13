#ifndef XBE_LIFE_SIGN_EVENT_HPP
#define XBE_LIFE_SIGN_EVENT_HPP 1

#include <xbe/event/XbeInstdEvent.hpp>

namespace xbe {
    namespace event {
        class LifeSignEvent : public xbe::event::XbeInstdEvent {
            public:
                LifeSignEvent() {}
                virtual ~LifeSignEvent() {}

                virtual std::string str() const {return "dummy";}
        };
    }
}

#endif // !XBE_LIFE_SIGN_EVENT_HPP

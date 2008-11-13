#ifndef XBE_LIFE_SIGN_EVENT_HPP
#define XBE_LIFE_SIGN_EVENT_HPP 1

#include <seda/UserEvent.hpp>

namespace xbe {
    namespace event {
        class LifeSignEvent : public seda::UserEvent {
            public:
                LifeSignEvent() {}
                virtual ~LifeSignEvent() {}

                virtual std::string str() const {return "dummy";}
        };
    }
}

#endif // !XBE_LIFE_SIGN_EVENT_HPP

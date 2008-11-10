#ifndef XBE_FINISHED_EVENT_HPP
#define XBE_FINISHED_EVENT_HPP 1

#include <seda/UserEvent.hpp>

namespace xbe {
    class FinishedEvent : public seda::UserEvent {
        public:
            FinishedEvent() {}
            virtual ~FinishedEvent() {}

            virtual std::string str() const {return "dummy";}
    };
}

#endif // !XBE_FINISHED_EVENT_HPP

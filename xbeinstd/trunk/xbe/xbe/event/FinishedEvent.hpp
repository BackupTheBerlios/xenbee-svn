#ifndef XBE_FINISHED_EVENT_HPP
#define XBE_FINISHED_EVENT_HPP 1

#include <xbe/event/XbeInstdEvent.hpp>

namespace xbe {
    namespace event {
        class FinishedEvent : public xbe::event::XbeInstdEvent {
            public:
                FinishedEvent() {}
                virtual ~FinishedEvent() {}

                virtual std::string str() const {return "dummy";}
        };
    }
}

#endif // !XBE_FINISHED_EVENT_HPP

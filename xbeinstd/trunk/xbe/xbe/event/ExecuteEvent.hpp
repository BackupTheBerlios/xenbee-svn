#ifndef XBE_EXECUTE_EVENT_HPP
#define XBE_EXECUTE_EVENT_HPP 1

#include <seda/UserEvent.hpp>

namespace xbe {
    namespace event {
        class ExecuteEvent : public seda::UserEvent {
            public:
                ExecuteEvent() {}
                virtual ~ExecuteEvent() {}

                virtual std::string str() const {return "dummy";}
        };
    }
}

#endif // !XBE_EXECUTE_EVENT_HPP

#ifndef XBE_status_EVENT_HPP
#define XBE_status_EVENT_HPP 1

#include <xbe/event/XbeInstdEvent.hpp>

namespace xbe {
    namespace event {
        class StatusEvent : public xbe::event::XbeInstdEvent {
            public:
                /*
                enum Status {
                    ST_UNKNOWN,
                    ST_IDLE,
                    ST_BUSY,
                    ST_WAIT_FIN_ACK,
                    ST_WAIT_JOB_TERM
                };
                */

                StatusEvent(const std::string &to, const std::string &from, const std::string &conversationID)
                : xbe::event::XbeInstdEvent(to, from, conversationID), state_("STATE NOT SET") {}
                virtual ~StatusEvent() {}

                virtual std::string str() const {return "status";}

                const std::string & state() const { return state_; }
                void state(const std::string &name) { state_ = name; }
            private:
                std::string state_;
        };
    }
}

#endif // !XBE_status_EVENT_HPP

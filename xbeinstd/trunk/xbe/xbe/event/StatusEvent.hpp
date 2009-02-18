#ifndef XBE_status_EVENT_HPP
#define XBE_status_EVENT_HPP 1

#include <xbe/event/XbeInstdEvent.hpp>

namespace xbe {
    namespace event {
        class StatusEvent : public xbe::event::XbeInstdEvent {
            public:
                typedef std::tr1::shared_ptr<StatusEvent> Ptr;

                enum Status {
                    ST_IDLE,
                    ST_BUSY,
                };

                StatusEvent(const std::string &to, const std::string &from, const std::string &conversationID, unsigned int timestamp = 0)
                : xbe::event::XbeInstdEvent(to, from, conversationID, timestamp),
                  state_(ST_IDLE), statusTaskExitCode_(-1) {}
                virtual ~StatusEvent() {}

                virtual std::string str() const {return "status";}

                const std::string & state() const {
                    static std::string IDLE("IDLE");
                    static std::string BUSY("BUSY");

                    switch (state_) {
                        case ST_IDLE:
                            return IDLE;
                        case ST_BUSY:
                            return BUSY;
                        default:
                            throw std::runtime_error("internal inconsistency detected - unknown state!");
                    }
                }
                void state(Status st) { state_ = st; }
                int taskStatusCode() const { return statusTaskExitCode_; }
                void taskStatusCode(int code) { statusTaskExitCode_ = code; }

                const std::string &taskStatusStdOut() const { return statusTaskOut_; }
                void taskStatusStdOut(const std::string &s) { statusTaskOut_ = s; }
                const std::string &taskStatusStdErr() const { return statusTaskErr_; }
                void taskStatusStdErr(const std::string &s) { statusTaskErr_ = s; }

            private:
                Status state_;
                int statusTaskExitCode_;
                std::string statusTaskOut_;
                std::string statusTaskErr_;
        };
    }
}

#endif // !XBE_status_EVENT_HPP

#ifndef XBE_status_EVENT_HPP
#define XBE_status_EVENT_HPP 1

#include <xbe/common.hpp>
#include <xbe/event/DecodedMessageEvent.hpp>

namespace xbe {
    namespace event {
        class StatusEvent : public xbe::event::DecodedMessageEvent {
            public:
                typedef std::tr1::shared_ptr<StatusEvent> Ptr;

                enum StatusCode {
                    ST_IDLE = 0,
                    ST_RUNNING,
                    ST_FINISHED,
                    ST_FAILED
                };

                explicit
                StatusEvent(const std::string &conversation_id, const mqs::Destination &dst = "", const mqs::Destination &src = "")
                : xbe::event::DecodedMessageEvent(conversation_id, "StatusEvent", dst, src),
                  XBE_INIT_LOGGER("StatusEvent"),
                  state_(ST_IDLE), statusTaskExitCode_(-1) {}
                virtual ~StatusEvent() {}

                virtual std::string str() const;
                virtual std::string serialize() const;
                static Ptr deserialize(const std::string &);

                const std::string & state_str() const {
                    static std::string IDLE("IDLE");
                    static std::string RUNNING("RUNNING");
                    static std::string FINISHED("FINISHED");
                    static std::string FAILED("FAILED");

                    switch (state_) {
                        case ST_IDLE:
                            return IDLE;
                        case ST_RUNNING:
                            return RUNNING;
                        case ST_FINISHED:
                            return FINISHED;
                        case ST_FAILED:
                            return FAILED;
                        default:
                            throw std::runtime_error("internal inconsistency detected - unknown state!");
                    }
                }
                StatusCode state() const { return state_; }
                void state(StatusCode st) { state_ = st; }
                int taskStatusCode() const { return statusTaskExitCode_; }
                void taskStatusCode(int code) { statusTaskExitCode_ = code; }

                const std::string &taskStatusStdOut() const { return statusTaskOut_; }
                void taskStatusStdOut(const std::string &s) { statusTaskOut_ = s; }
                const std::string &taskStatusStdErr() const { return statusTaskErr_; }
                void taskStatusStdErr(const std::string &s) { statusTaskErr_ = s; }

            private:
                XBE_DECLARE_LOGGER();
                StatusCode state_;
                int statusTaskExitCode_;
                std::string statusTaskOut_;
                std::string statusTaskErr_;
        };
    }
}

#endif // !XBE_status_EVENT_HPP

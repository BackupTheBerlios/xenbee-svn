#ifndef XBE_FAILED_EVENT_HPP
#define XBE_FAILED_EVENT_HPP 1

#include <xbe/common.hpp>
#include <xbe/event/DecodedMessageEvent.hpp>

namespace xbe {
    namespace event {
        class FailedEvent : public xbe::event::DecodedMessageEvent {
            public:
                typedef std::tr1::shared_ptr<FailedEvent> Ptr;

                enum FailReason {
                    UNKNOWN = 0
                };

                FailedEvent(const std::string &conversation_id, const mqs::Destination &dst="", const mqs::Destination &src="")
                : xbe::event::DecodedMessageEvent(conversation_id, "Failed", dst, src),
                  XBE_INIT_LOGGER("FailedEvent"),
                  task_(-1), reason_(UNKNOWN) {}
                virtual ~FailedEvent() {}

                virtual std::string str() const;
                virtual std::string serialize() const;
                static Ptr deserialize(const std::string &);

                FailedEvent *reason(FailReason r) { reason_ = r; return this; }
                FailReason reason() const { return reason_; }

                FailedEvent *task(int t) { task_ = t; return this; }
                int task() const { return task_; }
            private:
                XBE_DECLARE_LOGGER();
                int task_;
                FailReason reason_;
        };
    }
}

#endif // !XBE_FAILED_EVENT_HPP

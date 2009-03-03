#ifndef XBE_FAILED_ACK_EVENT_HPP
#define XBE_FAILED_ACK_EVENT_HPP 1

#include <xbe/common.hpp>
#include <xbe/event/DecodedMessageEvent.hpp>

namespace xbe {
    namespace event {
        class FailedAckEvent : public DecodedMessageEvent {
            public:
                typedef std::tr1::shared_ptr<FailedAckEvent> Ptr;

                FailedAckEvent(const std::string &conversation_id, const mqs::Destination &dst="", const mqs::Destination &src="")
                : DecodedMessageEvent(conversation_id, "FailedAck", dst, src),
                  XBE_INIT_LOGGER("FailedAckEvent"),
                  task_(-1) {}
                virtual ~FailedAckEvent() {}

                virtual std::string str() const;
                virtual std::string serialize() const;
                static Ptr deserialize(const std::string &s);

                FailedAckEvent *task(int tid) { task_ = tid; return this; }
                int task() const { return task_; }
            private:
                XBE_DECLARE_LOGGER();
                int task_;
        };
    }
}

#endif // !XBE_FAILED_ACK_EVENT_HPP

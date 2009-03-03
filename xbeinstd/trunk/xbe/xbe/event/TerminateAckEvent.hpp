#ifndef XBE_TERMINATE_ACK_EVENT_HPP
#define XBE_TERMINATE_ACK_EVENT_HPP 1

#include <xbe/common.hpp>
#include <xbe/event/DecodedMessageEvent.hpp>

namespace xbe {
    namespace event {
        class TerminateAckEvent : public xbe::event::DecodedMessageEvent {
            public:
                typedef std::tr1::shared_ptr<TerminateAckEvent> Ptr;

                TerminateAckEvent(const std::string &conversation_id, const mqs::Destination &dst="", const mqs::Destination &src="")
                : DecodedMessageEvent(conversation_id, "TerminateAck", dst, src),
                  XBE_INIT_LOGGER("TerminateAckEvent"), task_(-1) {}
                virtual ~TerminateAckEvent() {}

                virtual std::string str() const;
                virtual std::string serialize() const;
                static Ptr deserialize(const std::string &s);

                TerminateAckEvent *task(int t) { task_ = t; return this; }
                int task() const { return task_; }

//                template <class FSM> void execute(FSM &fsm) { fsm.TerminateAck(*this); }
            private:
                XBE_DECLARE_LOGGER();
                int task_;
        };
    }
}

#endif // !XBE_TERMINATE_ACK_EVENT_HPP

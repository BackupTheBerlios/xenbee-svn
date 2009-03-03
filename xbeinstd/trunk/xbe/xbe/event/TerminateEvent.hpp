#ifndef XBE_TERMINATE_EVENT_HPP
#define XBE_TERMINATE_EVENT_HPP 1

#include <xbe/common.hpp>
#include <xbe/event/DecodedMessageEvent.hpp>

namespace xbe {
    namespace event {
        class TerminateEvent : public xbe::event::DecodedMessageEvent {
            public:
                typedef std::tr1::shared_ptr<TerminateEvent> Ptr;

                TerminateEvent(const std::string &conversation_id, const mqs::Destination &dst="", const mqs::Destination &src="")
                : xbe::event::DecodedMessageEvent(conversation_id, "Terminate", dst, src),
                  XBE_INIT_LOGGER("TerminateEvent"), task_(-1) {}
                virtual ~TerminateEvent() {}

                virtual std::string str() const;
                virtual std::string serialize() const;
                static Ptr deserialize(const std::string &s);

                TerminateEvent *task(int t) { task_ = t; return this; }
                int task() const { return task_; }
            private:
                XBE_DECLARE_LOGGER();
                int task_;
        };
    }
}

#endif // !XBE_TERMINATE_EVENT_HPP

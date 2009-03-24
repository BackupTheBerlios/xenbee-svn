#ifndef XBE_FINISHED_EVENT_HPP
#define XBE_FINISHED_EVENT_HPP 1

#include <xbe/common/common.hpp>
#include <xbe/event/DecodedMessageEvent.hpp>

namespace xbe {
    namespace event {
        class FinishedEvent : public xbe::event::DecodedMessageEvent {
            public:
                typedef std::tr1::shared_ptr<FinishedEvent> Ptr;

                FinishedEvent(const std::string &conversation_id, const mqs::Destination &dst="", const mqs::Destination &src="")
                : xbe::event::DecodedMessageEvent(conversation_id, "FinishedEvent", dst, src),
                  XBE_INIT_LOGGER("FinishedEvent"),
                  exitcode_(0) {}

                virtual ~FinishedEvent() {}

                virtual std::string str() const;
                virtual std::string serialize() const;
                static Ptr deserialize(const std::string &s);

                FinishedEvent* exitcode(int ec) { exitcode_ = ec; return this; }
                int exitcode() const { return exitcode_; }
            private:
                XBE_DECLARE_LOGGER();
                int exitcode_;
        };
    }
}

#endif // !XBE_FINISHED_EVENT_HPP

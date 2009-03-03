#ifndef XBE_EXECUTE_NAK_EVENT_HPP
#define XBE_EXECUTE_NAK_EVENT_HPP 1

#include <xbe/common.hpp>
#include <xbe/event/DecodedMessageEvent.hpp>

namespace xbe {
    namespace event {
        class ExecuteNakEvent : public xbe::event::DecodedMessageEvent {
            public:
                typedef std::tr1::shared_ptr<ExecuteNakEvent> Ptr;

                enum ExecuteNakReason {
                    UNKNOWN_REASON = 0,
                    RESOURCE_BUSY = 1
                };

                ExecuteNakEvent(const std::string &conversation_id, const mqs::Destination &dst="", const mqs::Destination &src="")
                : xbe::event::DecodedMessageEvent(conversation_id, "ExecuteNakEvent", dst, src), XBE_INIT_LOGGER("ExecuteNakEvent"), reason_(UNKNOWN_REASON), detail_("") {}
                virtual ~ExecuteNakEvent() {}

                void reason(const ExecuteNakReason &r) { reason_ = r; }
                const ExecuteNakReason &reason() const { return reason_; }
                void detail(const std::string &d) { detail_ = d; }
                const std::string &detail() const { return detail_; }

                virtual std::string str() const;
                virtual std::string serialize() const;
                static Ptr deserialize(const std::string &);
            private:
                XBE_DECLARE_LOGGER();
                ExecuteNakReason reason_;
                std::string detail_;
        };
    }
}

#endif // !XBE_EXECUTE_ACK_EVENT_HPP

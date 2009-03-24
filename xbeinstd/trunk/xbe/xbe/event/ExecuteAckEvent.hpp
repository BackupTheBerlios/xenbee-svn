#ifndef XBE_EXECUTE_ACK_EVENT_HPP
#define XBE_EXECUTE_ACK_EVENT_HPP 1

#include <xbe/common/common.hpp>
#include <xbe/event/DecodedMessageEvent.hpp>

namespace xbe {
    namespace event {
        class ExecuteAckEvent : public xbe::event::DecodedMessageEvent {
            public:
                typedef std::tr1::shared_ptr<ExecuteAckEvent> Ptr;
                ExecuteAckEvent(const std::string &conversation_id, const mqs::Destination &dst="", const mqs::Destination &src="")
                : xbe::event::DecodedMessageEvent(conversation_id, "ExecuteAckEvent", dst, src), XBE_INIT_LOGGER("ExecuteAckEvent") {}
                virtual ~ExecuteAckEvent() {}

                virtual std::string str() const;
                virtual std::string serialize() const;
                static Ptr deserialize(const std::string &);
            private:
                XBE_DECLARE_LOGGER();
        };
    }
}

#endif // !XBE_EXECUTE_ACK_EVENT_HPP

#ifndef XBE_shutdownack_EVENT_HPP
#define XBE_shutdownack_EVENT_HPP 1

#include <xbe/common.hpp>
#include <xbe/event/DecodedMessageEvent.hpp>

namespace xbe {
    namespace event {
        class ShutdownAckEvent : public xbe::event::DecodedMessageEvent {
            public:
                typedef std::tr1::shared_ptr<ShutdownAckEvent> Ptr;

                ShutdownAckEvent(const std::string &conv_id, const mqs::Destination &dst="", const mqs::Destination &src="")
                : DecodedMessageEvent(conv_id, "ShutdownAck", dst, src),
                  XBE_INIT_LOGGER("ShutdownAckEvent") {}
                virtual ~ShutdownAckEvent() {}

                virtual std::string str() const;
                virtual std::string serialize() const;
                static Ptr deserialize(const std::string &);
            private:
                XBE_DECLARE_LOGGER();
        };
    }
}

#endif // !XBE_shutdownack_EVENT_HPP

#ifndef XBE_EVENT_ENCODED_MESSAGE_EVENT_HPP
#define XBE_EVENT_ENCODED_MESSAGE_EVENT_HPP 1

#include <xbe/event/MessageEvent.hpp>

namespace xbe {
namespace event {
    class EncodedMessageEvent : public xbe::event::MessageEvent {
    public:
        typedef std::tr1::shared_ptr<EncodedMessageEvent> Ptr;

        explicit
        EncodedMessageEvent(const std::string &msg,
                            const mqs::Destination &dst = "",
                            const mqs::Destination &src = "")
            : xbe::event::MessageEvent(msg, dst, src) {
        }
        virtual ~EncodedMessageEvent() {}
    };
}}

#endif // ! XBE_EVENT_ENCODED_MESSAGE_EVENT_HPP

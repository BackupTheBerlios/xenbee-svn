#ifndef XBE_EVENT_DECODED_MESSAGE_EVENT_HPP
#define XBE_EVENT_DECODED_MESSAGE_EVENT_HPP 1

#include <xbe/event/MessageEvent.hpp>
#include <string>

namespace xbe {
namespace event {
    class DecodedMessageEvent : public xbe::event::MessageEvent {
    public:
        typedef std::tr1::shared_ptr<DecodedMessageEvent> Ptr;
        
        virtual std::string serialize() const = 0;
        const std::string &conversation_id() const { return conversation_id_; }
    protected:
        DecodedMessageEvent(const std::string &conversation_id,
                            const std::string &msg,
                            const mqs::Destination &dst = "",
                            const mqs::Destination &src = "")
            : xbe::event::MessageEvent(msg, dst, src),
              conversation_id_(conversation_id) {
        }
    public:
        virtual ~DecodedMessageEvent() {}
    private:
        std::string conversation_id_;
    };
}}

#endif // ! XBE_EVENT_DECODED_MESSAGE_EVENT_HPP


